#specfile originally created for Fedora, modified for MeeGo Linux
%define db_version 4.6.21
%define pam_redhat_version 0.99.10-1


Summary: A security tool which provides authentication for applications
Name: pam
Version: 1.1.1
Release: 1
# The library is BSD licensed with option to relicense as GPLv2+ - this option is redundant
# as the BSD license allows that anyway. pam_timestamp and pam_console modules are GPLv2+,
# pam_rhosts_auth module is BSD with advertising
License: BSD and GPLv2+ and BSD with advertising
Group: System/Base
Source0: http://ftp.us.kernel.org/pub/linux/libs/pam/library/Linux-PAM-%{version}.tar.bz2
Source1: http://ftp.us.kernel.org/pub/linux/libs/pam/library/Linux-PAM-%{version}.tar.bz2.sign
Source2: https://fedorahosted.org/releases/p/a/pam-redhat/pam-redhat-%{pam_redhat_version}.tar.bz2
Source4: http://download.oracle.com/berkeley-db/db-%{db_version}.tar.gz
Source5: other.pamd
Source6: system-auth.pamd
Source7: config-util.pamd
Source8: dlopen.sh
Source9: system-auth.5
Source10: config-util.5
Source11: 90-nproc.conf
Source12: 60-non-root-X.perms
# MeeGo extensions
Source100: install-pam-module.sh

Patch1:  pam-1.0.90-redhat-modules.patch
Patch2:  db-4.6.18-glibc.patch
Patch4:  pam-0.99.8.1-dbpam.patch
Patch5:  pam-1.0.91-std-noclose.patch

Patch21: pam-0.99.10.0-unix-audit-failed.patch
Patch32: pam-0.99.3.0-tally-fail-close.patch
Patch33: pam-fix-console-regexp.patch
Patch34: pam-fix-security-problem.patch

%define _sbindir /sbin
%define _moduledir /%{_lib}/security
%define _secconfdir %{_sysconfdir}/security
%define _pamconfdir %{_sysconfdir}/pam.d

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires(post): ldconfig, coreutils
Requires(postun): ldconfig
BuildRequires: db4-devel
BuildRequires: bison, flex
BuildRequires: zlib-devel

URL: http://www.us.kernel.org/pub/linux/libs/pam/index.html

# We internalize libdb to get a non-threaded copy, but we should at least try
# to coexist with the system's copy of libdb, which will be used to make the
# files for use by pam_userdb (either by db_load or Perl's DB_File module).
# The non-threaded db4 is necessary so we do not break single threaded
# services when they call pam_userdb.so module.

%description
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication.


%package modules-userdb
Group: Development/Libraries
Summary: PAM userdb module
Requires: pam = %{version}-%{release}

%description modules-userdb
PAM userdb module

%package devel
Group: Development/Libraries
Summary: Files needed for developing PAM-aware applications and modules for PAM
Requires: pam = %{version}-%{release}

%description devel
PAM (Pluggable Authentication Modules) is a system security tool that
allows system administrators to set authentication policy without
having to recompile programs that handle authentication. This package
contains header files and static libraries used for building both
PAM-aware applications and modules for use with PAM.

%prep
%setup -q -n Linux-PAM-%{version} -a 2 -a 4

# Add custom modules.
mv pam-redhat-%{pam_redhat_version}/* modules

%patch1 -p1 -b .redhat-modules
pushd db-%{db_version}
%patch2 -p1 -b .db4-glibc
popd
%patch4 -p1 -b .dbpam
%patch5 -p1 -b .std-noclose

%patch32 -p1 -b .fail-close
%patch33 -p1 -b .ttysingledigit
%patch34 -p1 -b .pam-fix-security-problem

libtoolize --copy --force && aclocal && autoheader
autoreconf
chmod +x %{SOURCE8}

%build
CFLAGS="-fPIC $RPM_OPT_FLAGS" ; export CFLAGS

topdir=`pwd`/pam-instroot
test -d ${topdir}         || mkdir ${topdir}
test -d ${topdir}/include || mkdir ${topdir}/include
test -d ${topdir}/%{_lib} || mkdir ${topdir}/%{_lib}

pushd db-%{db_version}/build_unix
echo db_cv_mutex=UNIX/fcntl > config.cache
../dist/configure -C \
	--disable-compat185 \
	--disable-cxx \
	--disable-diagnostic \
	--disable-dump185 \
	--disable-java \
	--disable-rpc \
	--disable-tcl \
	--disable-shared \
	--with-pic \
	--with-uniquename=_pam \
	--with-mutex="UNIX/fcntl" \
	--prefix=${topdir} \
	--includedir=${topdir}/include \
	--libdir=${topdir}/%{_lib}
make
make install
popd

CPPFLAGS=-I${topdir}/include ; export CPPFLAGS
export LIBNAME="%{_lib}"
LDFLAGS=-L${topdir}/%{_lib} ; export LDFLAGS
%configure \
	--libdir=/%{_lib} \
	--includedir=%{_includedir}/security \
	--enable-isadir=../..%{_moduledir} \
	--disable-audit \
	--with-db-uniquename=_pam
make
# we do not use _smp_mflags because the build of sources in yacc/flex fails

%install
rm -rf $RPM_BUILD_ROOT

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
install -m 644 %{SOURCE7} $RPM_BUILD_ROOT%{_pamconfdir}/config-util
install -m 644 %{SOURCE11} $RPM_BUILD_ROOT%{_secconfdir}/limits.d/90-nproc.conf
install -m 644 %{SOURCE12} $RPM_BUILD_ROOT%{_secconfdir}/console.perms.d/60-non-root-X.perms
install -m 600 /dev/null $RPM_BUILD_ROOT%{_secconfdir}/opasswd
install -d -m 755 $RPM_BUILD_ROOT/var/log
install -m 600 /dev/null $RPM_BUILD_ROOT/var/log/faillog
install -m 600 /dev/null $RPM_BUILD_ROOT/var/log/tallylog

# Install man pages.
install -m 644 %{SOURCE9} %{SOURCE10} $RPM_BUILD_ROOT%{_mandir}/man5/

for phase in auth acct passwd session ; do
	ln -sf pam_unix.so $RPM_BUILD_ROOT%{_moduledir}/pam_unix_${phase}.so 
done

# Remove .la files and make new .so links -- this depends on the value
# of _libdir not changing, and *not* being /usr/lib.
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}
for lib in libpam libpamc libpam_misc ; do
pushd $RPM_BUILD_ROOT%{_libdir}
ln -sf ../../%{_lib}/${lib}.so.*.* ${lib}.so
popd
rm -f $RPM_BUILD_ROOT/%{_lib}/${lib}.so
rm -f $RPM_BUILD_ROOT/%{_lib}/${lib}.la
done
rm -f $RPM_BUILD_ROOT%{_moduledir}/*.la

# Duplicate doc file sets.
rm -fr $RPM_BUILD_ROOT/usr/share/doc/pam

# Create /lib/security in case it isn't the same as %{_moduledir}.
install -m755 -d $RPM_BUILD_ROOT/lib/security

# Install MeeGo extensions
# (%{_sbindir} was defined earlier without using %{_prefix}, and we
# don't want to install this script into /sbin so we add our own
# _prefix)
mkdir -p $RPM_BUILD_ROOT%{_prefix}%{_sbindir}
install -m 755 %{SOURCE100} $RPM_BUILD_ROOT%{_prefix}%{_sbindir}

%find_lang Linux-PAM
mv Linux-PAM.lang pam.lang

%check
# Make sure every module subdirectory gave us a module.  Yes, this is hackish.
for dir in modules/pam_* ; do
if [ -d ${dir} ] ; then
        [ ${dir} = "modules/pam_selinux" ] && continue
        [ ${dir} = "modules/pam_cracklib" ] && continue
        [ ${dir} = "modules/pam_postgresok" ] && continue
        [ ${dir} = "modules/pam_sepermit" ] && continue
        [ ${dir} = "modules/pam_tty_audit" ] && continue
	if ! ls -1 $RPM_BUILD_ROOT%{_moduledir}/`basename ${dir}`*.so ; then
		echo ERROR `basename ${dir}` did not build a module.
		exit 1
	fi
fi
done

# Check for module problems.  Specifically, check that every module we just
# installed can actually be loaded by a minimal PAM-aware application.
/sbin/ldconfig -n $RPM_BUILD_ROOT/%{_lib}
for module in $RPM_BUILD_ROOT%{_moduledir}/pam*.so ; do
	if ! env LD_LIBRARY_PATH=$RPM_BUILD_ROOT/%{_lib} \
		 %{SOURCE8} -ldl -lpam -L$RPM_BUILD_ROOT/%{_libdir} ${module} ; then
		echo ERROR module: ${module} cannot be loaded.
		exit 1
	fi
# And for good measure, make sure that none of the modules pull in threading
# libraries, which if loaded in a non-threaded application, can cause Very
# Bad Things to happen.
	if env LD_LIBRARY_PATH=$RPM_BUILD_ROOT/%{_lib} \
	       LD_PRELOAD=$RPM_BUILD_ROOT%{_libdir}/libpam.so ldd -r ${module} | fgrep -q libpthread ; then
		echo ERROR module: ${module} pulls threading libraries.
		exit 1
	fi
done

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig
if [ ! -a /var/log/faillog ] ; then
	[ -x /usr/bin/install ] && /usr/bin/install -m 600 /dev/null /var/log/faillog
fi
if [ ! -a /var/log/tallylog ] ; then
	[ -x /usr/bin/install ]  && /usr/bin/install -m 600 /dev/null /var/log/tallylog
fi

%postun -p /sbin/ldconfig


%lang_package

%files 
%defattr(-,root,root,-)
%dir %{_pamconfdir}
%config(noreplace) %{_pamconfdir}/other
%config(noreplace) %{_pamconfdir}/system-auth
%config(noreplace) %{_pamconfdir}/config-util
%doc Copyright
/%{_lib}/libpam.so.*
/%{_lib}/libpamc.so.*
/%{_lib}/libpam_misc.so.*
%{_sbindir}/pam_console_apply
%{_sbindir}/pam_tally
%{_sbindir}/pam_tally2
%{_prefix}%{_sbindir}/install-pam-module.sh
%attr(4755,root,root) %{_sbindir}/pam_timestamp_check
%attr(4755,root,root) %{_sbindir}/unix_chkpwd
%attr(0700,root,root) %{_sbindir}/unix_update
%attr(0755,root,root) %{_sbindir}/mkhomedir_helper
%if %{_lib} != lib
%dir /lib/security
%endif
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
%{_moduledir}/pam_pwhistory.so
%{_moduledir}/pam_rhosts.so
%{_moduledir}/pam_rootok.so
%{_moduledir}/pam_securetty.so
%{_moduledir}/pam_shells.so
%{_moduledir}/pam_stress.so
%{_moduledir}/pam_succeed_if.so
%{_moduledir}/pam_tally.so
%{_moduledir}/pam_tally2.so
%{_moduledir}/pam_time.so
%{_moduledir}/pam_timestamp.so
%{_moduledir}/pam_umask.so
%{_moduledir}/pam_unix.so
%{_moduledir}/pam_unix_acct.so
%{_moduledir}/pam_unix_auth.so
%{_moduledir}/pam_unix_passwd.so
%{_moduledir}/pam_unix_session.so
%{_moduledir}/pam_warn.so
%{_moduledir}/pam_wheel.so
%{_moduledir}/pam_xauth.so
%{_moduledir}/pam_filter
%dir %{_secconfdir}
%config(noreplace) %{_secconfdir}/access.conf
%config(noreplace) %{_secconfdir}/chroot.conf
%config %{_secconfdir}/console.perms
%config(noreplace) %{_secconfdir}/console.handlers
%config(noreplace) %{_secconfdir}/group.conf
%config(noreplace) %{_secconfdir}/limits.conf
%dir %{_secconfdir}/limits.d
%config(noreplace) %{_secconfdir}/limits.d/90-nproc.conf
%config(noreplace) %{_secconfdir}/namespace.conf
%dir %{_secconfdir}/namespace.d
%attr(755,root,root) %config(noreplace) %{_secconfdir}/namespace.init
%config(noreplace) %{_secconfdir}/pam_env.conf
%config(noreplace) %{_secconfdir}/time.conf
%config(noreplace) %{_secconfdir}/opasswd
%dir %{_secconfdir}/console.apps
%dir %{_secconfdir}/console.perms.d
%config %{_secconfdir}/console.perms.d/50-default.perms
%config %{_secconfdir}/console.perms.d/60-non-root-X.perms
%dir /var/run/console
%dir /var/run/sepermit
%ghost %verify(not md5 size mtime) /var/log/faillog
%ghost %verify(not md5 size mtime) /var/log/tallylog



%files modules-userdb
%defattr(-,root,root)
%{_moduledir}/pam_userdb.so

%files devel
%defattr(-,root,root)
%{_includedir}/security/
%doc %{_mandir}/man3/*
%doc %{_mandir}/man5/*
%doc %{_mandir}/man8/*
%{_libdir}/libpam.so
%{_libdir}/libpamc.so
%{_libdir}/libpam_misc.so
