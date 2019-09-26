%define pam_redhat_version 0.99.10-1

Summary: An extensible library which provides authentication for applications
Name: pam
Version: 1.1.8
Release: 2%{?dist}
# The library is BSD licensed with option to relicense as GPLv2+
# - this option is redundant as the BSD license allows that anyway.
# pam_timestamp, pam_loginuid, and pam_console modules are GPLv2+.
License: BSD and GPLv2+
Group: System Environment/Base
Source0: %{name}-%{version}.tar.bz2
# This is the old location that might be revived in future:
#Source0: http://ftp.us.kernel.org/pub/linux/libs/pam/library/Linux-PAM-%{version}.tar.bz2
#Source1: http://ftp.us.kernel.org/pub/linux/libs/pam/library/Linux-PAM-%{version}.tar.bz2.sign
Source2: https://fedorahosted.org/releases/p/a/pam-redhat/pam-redhat-%{pam_redhat_version}.tar.bz2
Source5: other.pamd
Source6: system-auth.pamd
Source7: password-auth.pamd
Source8: fingerprint-auth.pamd
Source9: smartcard-auth.pamd
Source10: config-util.pamd
Source11: dlopen.sh
Source12: system-auth.5
Source13: config-util.5
Source14: 90-nproc.conf
Source15: pamtmp.conf
Source16: postlogin.pamd
Source17: postlogin.5
Patch1:  pam-1.0.90-redhat-modules.patch
Patch2:  pam-1.1.6-std-noclose.patch
Patch4:  pam-1.1.0-console-nochmod.patch
Patch5:  pam-1.1.0-notally.patch
Patch7:  pam-1.1.0-console-fixes.patch
Patch8:  pam-1.1.1-faillock.patch
Patch9:  pam-1.1.6-noflex.patch
Patch10: pam-1.1.3-nouserenv.patch
Patch11: pam-1.1.3-console-abstract.patch
Patch12: pam-1.1.3-faillock-screensaver.patch
Patch13: pam-1.1.6-limits-user.patch
Patch15: pam-1.1.6-full-relro.patch
# FIPS related - non upstreamable
Patch20: pam-1.1.5-unix-no-fallback.patch
# Upstreamed partially
Patch29: pam-1.1.6-pwhistory-helper.patch
Patch31: pam-1.1.6-use-links.patch
Patch32: pam-1.1.7-tty-audit-init.patch
Patch33: pam-1.1.8-nodocs.patch

%define _pamlibdir /lib/
%define _moduledir /lib/security
%define _secconfdir %{_sysconfdir}/security
%define _pamconfdir %{_sysconfdir}/pam.d

%if %{?WITH_AUDIT:0}%{!?WITH_AUDIT:1}
%define WITH_AUDIT 1
%endif

Requires(post): coreutils, /sbin/ldconfig
BuildRequires: autoconf >= 2.60
BuildRequires: automake, libtool
BuildRequires: bison, flex, sed
BuildRequires: perl, pkgconfig, gettext-devel
Requires: glibc >= 2.3.90-37
BuildRequires: db4-devel

URL: http://www.linux-pam.org/

Obsoletes: pam-modules-userdb <= 1.1.1
Provides:  pam-modules-userdb = %{version}

%description
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication.

%package devel
Group: Development/Libraries
Summary: Files needed for developing PAM-aware applications and modules for PAM
Requires: pam%{?_isa} = %{version}-%{release}

%description devel
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication. This package
contains header files used for building both PAM-aware applications
and modules for use with the PAM system.

%package doc
Summary:   Documentation for %{name}
Group:     Documentation
Requires:  %{name} = %{version}-%{release}

%description doc
Man pages for %{name}.

%prep
%setup -q -n %{name}-%{version}/pam

tar xf %{SOURCE2}

perl -pi -e "s/ppc64-\*/ppc64-\* \| ppc64p7-\*/" build-aux/config.sub

# Add custom modules.
mv pam-redhat-%{pam_redhat_version}/* modules

%patch1 -p1 -b .redhat-modules
%patch2 -p1 -b .std-noclose
%patch4 -p1 -b .nochmod
%patch5 -p1 -b .notally
%patch7 -p1 -b .console-fixes
%patch8 -p1 -b .faillock
%patch9 -p1 -b .noflex
%patch10 -p1 -b .nouserenv
%patch11 -p1 -b .abstract
%patch12 -p1 -b .screensaver
%patch13 -p1 -b .limits
%patch15 -p1 -b .relro
%patch20 -p1 -b .no-fallback
%patch29 -p1 -b .pwhhelper
%patch31 -p1 -b .links
%patch32 -p1 -b .tty-audit-init
%patch33 -p1

%build
touch ChangeLog

# Create dummy man pages to get pass docbook
find ./ -name '*.?.xml' | xargs printf "touch \`echo %s | sed 's/.xml//g'\`\n" | sh

autoreconf -v -f -i
%configure \
	--libdir=%{_pamlibdir} \
	--includedir=%{_includedir}/security \
	--disable-selinux \
	--disable-audit \
	--disable-static \
	--disable-prelude \
	--disable-nis
make
# we do not use _smp_mflags because the build of sources in yacc/flex fails

%install
mkdir -p doc/txts
for readme in modules/pam_*/README ; do
	cp -f ${readme} doc/txts/README.`dirname ${readme} | sed -e 's|^modules/||'`
done

# Install the binaries, libraries, and modules.
make install DESTDIR=$RPM_BUILD_ROOT LDCONFIG=:

# RPM uses docs from source tree
rm -rf $RPM_BUILD_ROOT%{_datadir}/doc/Linux-PAM
# Included in setup package
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/environment

# Install default configuration files.
install -d -m 755 $RPM_BUILD_ROOT%{_pamconfdir}
install -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{_pamconfdir}/other
install -m 644 %{SOURCE6} $RPM_BUILD_ROOT%{_pamconfdir}/system-auth
install -m 644 %{SOURCE7} $RPM_BUILD_ROOT%{_pamconfdir}/password-auth
install -m 644 %{SOURCE8} $RPM_BUILD_ROOT%{_pamconfdir}/fingerprint-auth
install -m 644 %{SOURCE9} $RPM_BUILD_ROOT%{_pamconfdir}/smartcard-auth
install -m 644 %{SOURCE10} $RPM_BUILD_ROOT%{_pamconfdir}/config-util
install -m 644 %{SOURCE16} $RPM_BUILD_ROOT%{_pamconfdir}/postlogin
install -m 644 %{SOURCE14} $RPM_BUILD_ROOT%{_secconfdir}/limits.d/90-nproc.conf
install -m 600 /dev/null $RPM_BUILD_ROOT%{_secconfdir}/opasswd
install -d -m 755 $RPM_BUILD_ROOT/var/log
install -m 600 /dev/null $RPM_BUILD_ROOT/var/log/tallylog
install -d -m 755 $RPM_BUILD_ROOT/var/run/faillock

# Install man pages.
install -m 644 %{SOURCE12} %{SOURCE13} %{SOURCE17} $RPM_BUILD_ROOT%{_mandir}/man5/
ln -sf system-auth.5 $RPM_BUILD_ROOT%{_mandir}/man5/password-auth.5
ln -sf system-auth.5 $RPM_BUILD_ROOT%{_mandir}/man5/fingerprint-auth.5
ln -sf system-auth.5 $RPM_BUILD_ROOT%{_mandir}/man5/smartcard-auth.5


for phase in auth acct passwd session ; do
	ln -sf pam_unix.so $RPM_BUILD_ROOT%{_moduledir}/pam_unix_${phase}.so 
done

# Remove .la files and make new .so links -- this depends on the value
# of _libdir not changing, and *not* being /usr/lib.
for lib in libpam libpamc libpam_misc ; do
rm -f $RPM_BUILD_ROOT%{_pamlibdir}/${lib}.la
done
rm -f $RPM_BUILD_ROOT%{_moduledir}/*.la

%if "%{_pamlibdir}" != "%{_libdir}"
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}
for lib in libpam libpamc libpam_misc ; do
pushd $RPM_BUILD_ROOT%{_libdir}
ln -sf ../../lib/${lib}.so.*.* ${lib}.so
popd
rm -f $RPM_BUILD_ROOT%{_pamlibdir}/${lib}.so
done
%endif

rm -fr $RPM_BUILD_ROOT%{_docdir}/%{name}
mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
install -m0644 -t $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version} \
        doc/txts/* doc/specs/rfc86.0.txt

# Install the file for autocreation of /var/run subdirectories on boot
install -m644 -D %{SOURCE15} $RPM_BUILD_ROOT%{_prefix}/lib/tmpfiles.d/pam.conf

%find_lang Linux-PAM

%check
# Make sure every module subdirectory gave us a module.  Yes, this is hackish.
for dir in modules/pam_* ; do
if [ -d ${dir} ] ; then
        [ ${dir} = "modules/pam_selinux" ] && continue
        [ ${dir} = "modules/pam_sepermit" ] && continue
        [ ${dir} = "modules/pam_tty_audit" ] && continue
	[ ${dir} = "modules/pam_cracklib" ] && continue
	[ ${dir} = "modules/pam_tally" ] && continue
	if ! ls -1 $RPM_BUILD_ROOT%{_moduledir}/`basename ${dir}`*.so ; then
		echo ERROR `basename ${dir}` did not build a module.
		exit 1
	fi
fi
done

chmod 755 %{SOURCE11}

# Check for module problems.  Specifically, check that every module we just
# installed can actually be loaded by a minimal PAM-aware application.
/sbin/ldconfig -n $RPM_BUILD_ROOT%{_pamlibdir}
for module in $RPM_BUILD_ROOT%{_moduledir}/pam*.so ; do
	if ! env LD_LIBRARY_PATH=$RPM_BUILD_ROOT%{_pamlibdir} \
		 %{SOURCE11} -ldl -lpam -L$RPM_BUILD_ROOT%{_libdir} ${module} ; then
		echo ERROR module: ${module} cannot be loaded.
		exit 1
	fi
done

%post
/sbin/ldconfig
if [ ! -e /var/log/tallylog ] ; then
	install -m 600 /dev/null /var/log/tallylog
fi

%postun -p /sbin/ldconfig

%files -f Linux-PAM.lang
%defattr(-,root,root)
%license Copyright
%dir %{_pamconfdir}
%config %{_pamconfdir}/other
%config %{_pamconfdir}/system-auth
%config %{_pamconfdir}/password-auth
%config %{_pamconfdir}/fingerprint-auth
%config %{_pamconfdir}/smartcard-auth
%config %{_pamconfdir}/config-util
%config %{_pamconfdir}/postlogin
%{_pamlibdir}/libpam.so.*
%{_pamlibdir}/libpamc.so.*
%{_pamlibdir}/libpam_misc.so.*
%{_sbindir}/pam_console_apply
%{_sbindir}/pam_tally2
%{_sbindir}/faillock
%attr(4755,root,root) %{_sbindir}/pam_timestamp_check
%attr(4755,root,root) %{_sbindir}/unix_chkpwd
%attr(0700,root,root) %{_sbindir}/unix_update
%attr(0755,root,root) %{_sbindir}/mkhomedir_helper
%attr(0755,root,root) %{_sbindir}/pwhistory_helper
%dir %{_moduledir}
%{_moduledir}/pam_access.so
%{_moduledir}/pam_chroot.so
%{_moduledir}/pam_console.so
%{_moduledir}/pam_debug.so
%{_moduledir}/pam_deny.so
%{_moduledir}/pam_echo.so
%{_moduledir}/pam_env.so
%{_moduledir}/pam_exec.so
%{_moduledir}/pam_faildelay.so
%{_moduledir}/pam_faillock.so
%{_moduledir}/pam_filter.so
%{_moduledir}/pam_ftp.so
%{_moduledir}/pam_group.so
%{_moduledir}/pam_issue.so
%{_moduledir}/pam_keyinit.so
%{_moduledir}/pam_lastlog.so
%{_moduledir}/pam_limits.so
%{_moduledir}/pam_listfile.so
%{_moduledir}/pam_localuser.so
%{_moduledir}/pam_loginuid.so
%{_moduledir}/pam_mail.so
%{_moduledir}/pam_mkhomedir.so
%{_moduledir}/pam_motd.so
%{_moduledir}/pam_namespace.so
%{_moduledir}/pam_nologin.so
%{_moduledir}/pam_permit.so
%{_moduledir}/pam_postgresok.so
%{_moduledir}/pam_pwhistory.so
%{_moduledir}/pam_rhosts.so
%{_moduledir}/pam_rootok.so
%{_moduledir}/pam_securetty.so
%{_moduledir}/pam_shells.so
%{_moduledir}/pam_stress.so
%{_moduledir}/pam_succeed_if.so
%{_moduledir}/pam_tally2.so
%{_moduledir}/pam_time.so
%{_moduledir}/pam_timestamp.so
%{_moduledir}/pam_umask.so
%{_moduledir}/pam_unix.so
%{_moduledir}/pam_unix_acct.so
%{_moduledir}/pam_unix_auth.so
%{_moduledir}/pam_unix_passwd.so
%{_moduledir}/pam_unix_session.so
%{_moduledir}/pam_userdb.so
%{_moduledir}/pam_warn.so
%{_moduledir}/pam_wheel.so
%{_moduledir}/pam_xauth.so
%{_moduledir}/pam_filter
%dir %{_secconfdir}
%config %{_secconfdir}/access.conf
%config %{_secconfdir}/chroot.conf
%config %{_secconfdir}/console.perms
%config %{_secconfdir}/console.handlers
%config %{_secconfdir}/group.conf
%config %{_secconfdir}/limits.conf
%dir %{_secconfdir}/limits.d
%config %{_secconfdir}/limits.d/90-nproc.conf
%config %{_secconfdir}/namespace.conf
%dir %{_secconfdir}/namespace.d
%attr(755,root,root) %config %{_secconfdir}/namespace.init
%config %{_secconfdir}/pam_env.conf
%config %{_secconfdir}/time.conf
%config %{_secconfdir}/opasswd
%dir %{_secconfdir}/console.apps
%dir %{_secconfdir}/console.perms.d
%dir /var/run/console
%ghost %verify(not md5 size mtime) /var/log/tallylog
%dir /var/run/faillock
%{_prefix}/lib/tmpfiles.d/pam.conf

%files devel
%defattr(-,root,root)
%{_includedir}/security
%{_libdir}/libpam.so
%{_libdir}/libpamc.so
%{_libdir}/libpam_misc.so

%files doc
%defattr(-,root,root)
%{_mandir}/man5/*
%{_mandir}/man8/*
%{_docdir}/%{name}-%{version}
