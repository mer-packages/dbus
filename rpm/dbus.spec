# Conditional building of X11 related things
%bcond_with X11

Name:       dbus

%define dbus_user_uid 81

Summary:    D-Bus message bus
Version:    1.6.24
Release:    1
Group:      System/Libraries
License:    GPLv2+ or AFL
URL:        http://www.freedesktop.org/software/dbus/
Source0:    http://dbus.freedesktop.org/releases/%{name}/%{name}-%{version}.tar.gz
Source1:    dbus-user.socket
Source2:    dbus-user.service
Requires:   %{name}-libs = %{version}
Requires:   systemd
Requires(pre): /usr/sbin/useradd
Requires(preun): systemd
Requires(post): systemd
Requires(postun): systemd
BuildRequires:  expat-devel >= 1.95.5
BuildRequires:  gettext
BuildRequires:  libcap-devel
BuildRequires:  libtool
BuildRequires:  systemd-devel
%if %{with X11}
BuildRequires:  pkgconfig(x11)
%endif
Obsoletes:      %{name}-x11 < 1.6.20+git2
Provides:       %{name}-x11

%description
D-Bus is a system for sending messages between applications. It is used both
for the systemwide message bus service, and as a per-user-login-session
messaging facility.


%package libs
Summary:    Libraries for accessing D-Bus
Group:      System/Libraries
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description libs
Lowlevel libraries for accessing D-Bus.

%package doc
Summary:    Developer documentation for D-Bus
Group:      Documentation
Requires:   %{name} = %{version}-%{release}

%description doc
This package contains DevHelp developer documentation for D-Bus along with
other supporting documentation such as the introspect dtd file.


%package devel
Summary:    Libraries and headers for D-Bus
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}
Requires:   pkgconfig

%description devel
Headers and static libraries for D-Bus.


%prep
%setup -q -n %{name}-%{version}/dbus

%build

%reconfigure --disable-static \
    --exec-prefix=/ \
    --bindir=/bin \
    --libexecdir=/%{_lib}/dbus-1 \
    --sysconfdir=/etc \
    --disable-tests \
    --disable-asserts \
    --disable-xml-docs \
    --disable-doxygen-docs \
    --disable-selinux \
    --disable-libaudit \
    --with-system-pid-file=%{_localstatedir}/run/messagebus.pid \
    --with-dbus-user=dbus \
    --with-systemdsystemunitdir="/%{_lib}/systemd/system" \
%if %{with X11}
    --with-x \
%endif
    --enable-systemd

make %{?jobs:-j%jobs}

%install
rm -rf %{buildroot}
%make_install

mkdir -p %{buildroot}%{_bindir}
mv -f %{buildroot}/bin/dbus-launch %{buildroot}%{_bindir}

mkdir -p %{buildroot}%{_datadir}/dbus-1/interfaces

mkdir -p %{buildroot}%{_libdir}/systemd/user
install -m0644 %{SOURCE1} %{buildroot}%{_libdir}/systemd/user/dbus.socket
install -m0644 %{SOURCE2} %{buildroot}%{_libdir}/systemd/user/dbus.service

%pre
# Add the "dbus" user and group
[ -e /usr/sbin/groupadd ] && /usr/sbin/groupadd -r -g %{dbus_user_uid} dbus 2>/dev/null || :
[ -e /usr/sbin/useradd ] && /usr/sbin/useradd -c 'System message bus' -u %{dbus_user_uid} \
-g %{dbus_user_uid} -s /sbin/nologin -r -d '/' dbus 2> /dev/null || :

%preun
if [ "$1" -eq 0 ]; then
systemctl stop dbus.service || :
fi

%post
systemctl daemon-reload || :
# Do not restart dbus on post as it can cause a lot of services to break.
# We assume user is forced to reboot the system when system is updated.
systemctl reload dbus.service || :

%postun
systemctl daemon-reload || :

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%doc COPYING
/bin/dbus-cleanup-sockets
/bin/dbus-daemon
%{_bindir}/dbus-launch
/bin/dbus-monitor
/bin/dbus-send
/bin/dbus-uuidgen
%dir %{_sysconfdir}/dbus-1
%config(noreplace) %{_sysconfdir}/dbus-1/session.conf
%dir %{_sysconfdir}/dbus-1/session.d
%config(noreplace) %{_sysconfdir}/dbus-1/system.conf
%dir %{_sysconfdir}/dbus-1/system.d
%dir /%{_lib}/dbus-1
%{_libdir}/systemd/user/*
/lib/systemd/system/dbus.service
/lib/systemd/system/dbus.socket
/lib/systemd/system/dbus.target.wants/dbus.socket
/lib/systemd/system/basic.target.wants/dbus.service
/lib/systemd/system/sockets.target.wants/dbus.socket
%attr(4750,root,dbus) /%{_lib}/dbus-1/dbus-daemon-launch-helper
%dir %{_datadir}/dbus-1
%{_datadir}/dbus-1/interfaces
%{_datadir}/dbus-1/services
%{_datadir}/dbus-1/system-services
%doc %{_mandir}/man1/dbus-cleanup-sockets.1.gz
%doc %{_mandir}/man1/dbus-daemon.1.gz
%doc %{_mandir}/man1/dbus-launch.1.gz
%doc %{_mandir}/man1/dbus-monitor.1.gz
%doc %{_mandir}/man1/dbus-send.1.gz
%doc %{_mandir}/man1/dbus-uuidgen.1.gz
%ghost %dir %{_localstatedir}/run/dbus
%dir %{_localstatedir}/lib/dbus

%files libs
%defattr(-,root,root,-)
%{_libdir}/libdbus-1.so.3*

%files doc
%defattr(-,root,root,-)
%doc doc/introspect.dtd
%doc doc/introspect.xsl
%doc doc/system-activation.txt
%doc %{_datadir}/doc/dbus/diagram.png
%doc %{_datadir}/doc/dbus/diagram.svg
%doc %{_datadir}/doc/dbus/system-activation.txt

%files devel
%defattr(-,root,root,-)
%{_libdir}/libdbus-1.so
%{_includedir}/dbus-1.0/dbus/dbus*.h
%dir %{_libdir}/dbus-1.0
%{_libdir}/dbus-1.0/include/dbus/dbus-arch-deps.h
%{_libdir}/pkgconfig/dbus-1.pc
