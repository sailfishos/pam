Summary: An extensible library which provides authentication for applications
Name: pam
Version: 1.6.1
Release: 1
# The library is BSD licensed with option to relicense as GPLv2+
# - this option is redundant as the BSD license allows that anyway.
# pam_timestamp, pam_loginuid modules are GPLv2+.
License: BSD and GPLv2+
Source0: %{name}-%{version}.tar.xz
Source3: macros.%{name}
Source5: other.pamd
Source6: system-auth.pamd
Source7: password-auth.pamd
Source10: config-util.pamd
Source11: dlopen.sh
Source15: pamtmp.conf
Source16: postlogin.pamd

# https://github.com/linux-pam/linux-pam/commit/aabd5314a6d76968c377969b49118a2df3f97003
Patch5:  pam-1.6.1-pam-env-econf-read-file-fixes.patch

%{load:%{SOURCE3}}

### Dependencies ###
Requires(post): coreutils, /sbin/ldconfig
BuildRequires: autoconf >= 2.60
BuildRequires: automake, libtool
BuildRequires: bison, flex, sed
BuildRequires: perl, pkgconfig, gettext-devel
BuildRequires: pkgconfig(libcrypt)
BuildRequires: pkgconfig(systemd)
Provides: pam-doc >= 1.6.1
Obsoletes: pam-doc < 1.6.1

URL: http://www.linux-pam.org/

%description
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication.

%package devel
Summary: Files needed for developing PAM-aware applications and modules for PAM
Requires: pam%{?_isa} = %{version}-%{release}

%description devel
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication. This package
contains header files used for building both PAM-aware applications
and modules for use with the PAM system.

%prep
%autosetup -p1 -n %{name}-%{version}/pam

%build
touch ChangeLog

autoreconf -v -f -i
%configure \
	--libdir=%{_pam_libdir} \
	--includedir=%{_includedir}/security \
	--disable-rpath \
	--disable-selinux \
	--disable-audit \
	--disable-static \
	--disable-prelude \
	--disable-nis \
	--disable-doc \
	--enable-db=no

%make_build

%install
# Install the macros file
install -D -m 644 %{SOURCE3} %{buildroot}%{_rpmconfigdir}/macros.d/macros.%{name}

# Install the binaries, libraries, and modules.
%make_install LDCONFIG=:

# Included in setup package
rm -f %{buildroot}%{_sysconfdir}/environment

# Install default configuration files.
install -d -m 755 %{buildroot}%{_pam_confdir}
install -d -m 755 %{buildroot}%{_pam_vendordir}
install -m 644 %{SOURCE5} %{buildroot}%{_pam_confdir}/other
install -m 644 %{SOURCE6} %{buildroot}%{_pam_confdir}/system-auth
install -m 644 %{SOURCE7} %{buildroot}%{_pam_confdir}/password-auth
install -m 644 %{SOURCE10} %{buildroot}%{_pam_confdir}/config-util
install -m 644 %{SOURCE16} %{buildroot}%{_pam_confdir}/postlogin
install -m 600 /dev/null %{buildroot}%{_pam_secconfdir}/opasswd
install -d -m 755 %{buildroot}/var/log
install -d -m 755 %{buildroot}/var/run/faillock
install -d -m 755 %{buildroot}%{_sysconfdir}/motd.d
install -d -m 755 %{buildroot}/usr/lib/motd.d
install -d -m 755 %{buildroot}/run/motd.d

for phase in auth acct passwd session ; do
	ln -sf pam_unix.so %{buildroot}%{_pam_moduledir}/pam_unix_${phase}.so
done

# Remove .la files and make new .so links -- this depends on the value
# of _libdir not changing, and *not* being /usr/lib.
for lib in libpam libpamc libpam_misc ; do
rm -f %{buildroot}%{_pam_libdir}/${lib}.la
done
rm -f %{buildroot}%{_pam_moduledir}/*.la

%if "%{_pam_libdir}" != "%{_libdir}"
install -d -m 755 %{buildroot}%{_libdir}
for lib in libpam libpamc libpam_misc ; do
  pushd %{buildroot}%{_libdir}
  ln -sf %{_pam_libdir}/${lib}.so.*.* ${lib}.so
  popd
  rm -f %{buildroot}%{_pam_libdir}/${lib}.so
done
%endif

# Install the file for autocreation of /var/run subdirectories on boot
install -m644 -D %{SOURCE15} %{buildroot}%{_prefix}/lib/tmpfiles.d/pam.conf

# Install systemd unit file.
install -m644 -D modules/pam_namespace/pam_namespace.service \
  %{buildroot}%{_unitdir}/pam_namespace.service

%find_lang Linux-PAM

%check
# Make sure every module subdirectory gave us a module.  Yes, this is hackish.
for dir in modules/pam_* ; do
if [ -d ${dir} ] ; then
	[ ${dir} = "modules/pam_selinux" ] && continue
	[ ${dir} = "modules/pam_sepermit" ] && continue
	[ ${dir} = "modules/pam_tty_audit" ] && continue
	[ ${dir} = "modules/pam_userdb" ] && continue
	[ ${dir} = "modules/pam_lastlog" ] && continue
	if ! ls -1 %{buildroot}%{_pam_moduledir}/`basename ${dir}`*.so ; then
		echo ERROR `basename ${dir}` did not build a module.
		exit 1
	fi
fi
done

chmod 755 %{SOURCE11}

# Check for module problems.  Specifically, check that every module we just
# installed can actually be loaded by a minimal PAM-aware application.
/sbin/ldconfig -n %{buildroot}%{_pam_libdir}
for module in %{buildroot}%{_pam_moduledir}/pam*.so ; do
	if ! env LD_LIBRARY_PATH=%{buildroot}%{_pam_libdir} \
		 %{SOURCE11} -ldl -lpam -L%{buildroot}%{_libdir} ${module} ; then
		echo ERROR module: ${module} cannot be loaded.
		exit 1
	fi
done

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files -f Linux-PAM.lang
%license Copyright
%dir %{_pam_confdir}
%dir %{_pam_vendordir}
%config %{_pam_confdir}/other
%config %{_pam_confdir}/system-auth
%config %{_pam_confdir}/password-auth
%config %{_pam_confdir}/config-util
%{_rpmconfigdir}/macros.d/macros.%{name}
%config %{_pam_confdir}/postlogin
%{_pam_libdir}/libpam.so.*
%{_pam_libdir}/libpamc.so.*
%{_pam_libdir}/libpam_misc.so.*
%{_sbindir}/pam_namespace_helper
%{_sbindir}/faillock
%attr(4755,root,root) %{_sbindir}/pam_timestamp_check
%attr(4755,root,root) %{_sbindir}/unix_chkpwd
%attr(0755,root,root) %{_sbindir}/mkhomedir_helper
%dir %{_pam_moduledir}
%{_pam_moduledir}/pam_access.so
%{_pam_moduledir}/pam_canonicalize_user.so
%{_pam_moduledir}/pam_debug.so
%{_pam_moduledir}/pam_deny.so
%{_pam_moduledir}/pam_echo.so
%{_pam_moduledir}/pam_env.so
%{_pam_moduledir}/pam_exec.so
%{_pam_moduledir}/pam_faildelay.so
%{_pam_moduledir}/pam_faillock.so
%{_pam_moduledir}/pam_filter.so
%{_pam_moduledir}/pam_ftp.so
%{_pam_moduledir}/pam_group.so
%{_pam_moduledir}/pam_issue.so
%{_pam_moduledir}/pam_keyinit.so
%{_pam_moduledir}/pam_limits.so
%{_pam_moduledir}/pam_listfile.so
%{_pam_moduledir}/pam_localuser.so
%{_pam_moduledir}/pam_loginuid.so
%{_pam_moduledir}/pam_mail.so
%{_pam_moduledir}/pam_mkhomedir.so
%{_pam_moduledir}/pam_motd.so
%{_pam_moduledir}/pam_namespace.so
%{_pam_moduledir}/pam_nologin.so
%{_pam_moduledir}/pam_permit.so
%{_pam_moduledir}/pam_pwhistory.so
%{_pam_moduledir}/pam_rhosts.so
%{_pam_moduledir}/pam_rootok.so
%{_pam_moduledir}/pam_securetty.so
%{_pam_moduledir}/pam_setquota.so
%{_pam_moduledir}/pam_shells.so
%{_pam_moduledir}/pam_stress.so
%{_pam_moduledir}/pam_succeed_if.so
%{_pam_moduledir}/pam_time.so
%{_pam_moduledir}/pam_timestamp.so
%{_pam_moduledir}/pam_umask.so
%{_pam_moduledir}/pam_unix.so
%{_pam_moduledir}/pam_unix_acct.so
%{_pam_moduledir}/pam_unix_auth.so
%{_pam_moduledir}/pam_unix_passwd.so
%{_pam_moduledir}/pam_unix_session.so
%{_pam_moduledir}/pam_usertype.so
%{_pam_moduledir}/pam_warn.so
%{_pam_moduledir}/pam_wheel.so
%{_pam_moduledir}/pam_xauth.so
%{_pam_moduledir}/pam_filter
%{_unitdir}/pam_namespace.service
%dir %{_pam_secconfdir}
%config %{_pam_secconfdir}/access.conf
%config %{_pam_secconfdir}/faillock.conf
%config %{_pam_secconfdir}/group.conf
%config %{_pam_secconfdir}/limits.conf
%dir %{_pam_secconfdir}/limits.d
%config %{_pam_secconfdir}/namespace.conf
%dir %{_pam_secconfdir}/namespace.d
%attr(755,root,root) %config %{_pam_secconfdir}/namespace.init
%config %{_pam_secconfdir}/pam_env.conf
%config(noreplace) %{_pam_secconfdir}/pwhistory.conf
%config %{_pam_secconfdir}/time.conf
%config %{_pam_secconfdir}/opasswd
%dir /var/run/faillock
%{_prefix}/lib/tmpfiles.d/pam.conf

%files devel
%{_includedir}/security
%{_libdir}/libpam.so
%{_libdir}/libpamc.so
%{_libdir}/libpam_misc.so
%{_libdir}/pkgconfig/pam.pc
%{_libdir}/pkgconfig/pam_misc.pc
%{_libdir}/pkgconfig/pamc.pc
