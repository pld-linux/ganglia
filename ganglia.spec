# TODO
# - unpackaged
#   /etc/conf.d/modpython.conf
#   /etc/gmetad.conf
Summary:	Ganglia Distributed Monitoring System
Name:		ganglia
Version:	3.1.7
Release:	0.1
License:	BSD
Group:		Applications/Networking
URL:		http://www.ganglia.info/
Source0:	http://dl.sourceforge.net/ganglia/%{name}-%{version}.tar.gz
# Source0-md5:	6aa5e2109c2cc8007a6def0799cf1b4c
Source1:	%{name}-gmond.init
Source2:	%{name}-gmetad.init
Patch0:		%{name}-diskusage-fix.patch
BuildRequires:	apr-devel
BuildRequires:	expat-devel
BuildRequires:	freetype-devel
BuildRequires:	libart_lgpl-devel
BuildRequires:	libconfuse-devel
BuildRequires:	libpng-devel
BuildRequires:	python-devel
BuildRequires:	rrdtool-devel
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_webapps	/etc/webapps
%define		_webapp		%{name}

%description
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

%package web
Summary:	Ganglia Web Frontend
Group:		Applications/Networking
Requires:	%{name}-gmetad = %{version}-%{release}
Requires:	php-gd
Requires:	rrdtool
Requires:	webserver(php)

%description web
This package provides a web frontend to display the XML tree published
by ganglia, and to provide historical graphs of collected metrics.

This website is written in the PHP4 language.

%package gmetad
Summary:	Ganglia Metadata collection daemon
Group:		Applications/Networking
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires(preun):	/sbin/service
Requires:	%{name} = %{version}-%{release}

%description gmetad
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmetad daemon aggregates monitoring data from several clusters to
form a monitoring grid. It also keeps metric history using rrdtool.

%package gmond
Summary:	Ganglia Monitoring daemon
Group:		Applications/Networking
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires(preun):	/sbin/service
Requires:	%{name} = %{version}-%{release}

%description gmond
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmond daemon provides the ganglia service within a single cluster
or Multicast domain.

%package gmond-python
Summary:	Ganglia Monitor daemon python DSO and metric modules
Group:		Applications/Networking
Requires:	ganglia-gmond
Requires:	python

%description gmond-python
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This package provides the gmond python DSO and python gmond modules,
which can be loaded via the DSO at gmond daemon start time.

%package devel
Summary:	Ganglia Library
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}

%description devel
The Ganglia Monitoring Core library provides a set of functions that
programmers can use to build scalable cluster or grid applications

%prep
%setup -q
%patch -P0 -p0
## Hey, those shouldn't be executable...
chmod -x lib/*.{h,x}

cat << 'EOF' > apache.conf
#
# Ganglia monitoring system PHP web frontend
#

Alias /%{name} %{_datadir}/%{name}
<Location /%{name}>
	Order deny,allow
	Deny from all
	Allow from 127.0.0.1
	Allow from ::1
	# Allow from .example.com
</Location>
EOF

%build
%configure \
	--with-gmetad \
	--disable-static \
	--enable-shared

## Default to run as user ganglia instead of nobody
%{__perl} -pi.orig -e 's|nobody|ganglia|g' \
	lib/libgmond.c gmetad/conf.c gmond/g25_config.c \
	gmetad/gmetad.conf gmond/gmond.conf.html ganglia.html \
	gmond/conf.pod ganglia.pod README lib/default_conf.h

## Don't have initscripts turn daemons on by default
%{__perl} -pi.orig -e 's|2345|-|g' \
	gmond/gmond.init gmetad/gmetad.init

%{__make}

%install
rm -rf $RPM_BUILD_ROOT

## Put web files in place
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}
install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
cp -a web/* $RPM_BUILD_ROOT%{_datadir}/%{name}
mv $RPM_BUILD_ROOT%{_datadir}/%{name}/conf.php $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/conf.php
ln -s ../../..%{_sysconfdir}/%{name}/conf.php \
    $RPM_BUILD_ROOT%{_datadir}/%{name}/conf.php
mv $RPM_BUILD_ROOT%{_datadir}/%{name}/private_clusters $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
ln -s ../../..%{_sysconfdir}/%{name}/private_clusters \
    $RPM_BUILD_ROOT%{_datadir}/%{name}/private_clusters
install -d $RPM_BUILD_ROOT%{_webapps}/%{_webapp}
cp -a apache.conf $RPM_BUILD_ROOT%{_webapps}/%{_webapp}/apache.conf
cp -a apache.conf $RPM_BUILD_ROOT%{_webapps}/%{_webapp}/httpd.conf

## Create directory structures
install -d $RPM_BUILD_ROOT/etc/rc.d/init.d
install -d $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d
install -d $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/rrds
install -d $RPM_BUILD_ROOT%{_mandir}/man1
install -d $RPM_BUILD_ROOT%{_mandir}/man5
## Put files in place
install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/gmond
install %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/gmetad
cp -p gmond/gmond.conf.5 $RPM_BUILD_ROOT%{_mandir}/man5/gmond.conf.5
cp -p gmetad/gmetad.conf.in $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/gmetad.conf
cp -p mans/*.1 $RPM_BUILD_ROOT%{_mandir}/man1
## Build default gmond.conf from gmond using the '-t' flag
gmond/gmond -t | %{__perl} -pe 's|nobody|ganglia|g' > $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/gmond.conf

## Python bits
# Copy the python metric modules and .conf files
cp -p gmond/python_modules/conf.d/*.pyconf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d
cp -p gmond/modules/conf.d/*.conf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d
cp -p gmond/python_modules/*/*.py $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules
# Don't install the example modules
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/example.conf
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/example.pyconf
# Don't install the status modules
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/modgstatus.conf
# Clean up the .conf.in files
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/*.conf.in
## Disable the diskusage module until it is configured properly
#mv $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf.off

## Install binaries
%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT
## House cleaning
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_datadir}/%{name}/{Makefile.am,version.php.in}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
/sbin/ldconfig
%groupadd -g 206 ganglia
%useradd -u 206 -c "Ganglia Monitoring System" -s /sbin/nologin -g ganglia -r -d %{_localstatedir}/lib/%{name} ganglia

%post -p /sbin/ldconfig

%post gmond
/sbin/chkconfig --add gmond

%post gmetad
/sbin/chkconfig --add gmetad

%preun gmetad
if [ "$1" = 0 ]; then
	%service gmetad stop
	/sbin/chkconfig --del gmetad
fi

%preun gmond
if [ "$1" = 0 ]; then
	%service gmond stop
	/sbin/chkconfig --del gmond
fi

%post	devel -p /sbin/ldconfig
%postun	devel -p /sbin/ldconfig

%triggerin web -- apache1 < 1.3.37-3, apache1-base
%webapp_register apache %{_webapp}

%triggerun web -- apache1 < 1.3.37-3, apache1-base
%webapp_unregister apache %{_webapp}

%triggerin web -- apache < 2.2.0, apache-base
%webapp_register httpd %{_webapp}

%triggerun web -- apache < 2.2.0, apache-base
%webapp_unregister httpd %{_webapp}

%files
%defattr(644,root,root,755)
%doc AUTHORS COPYING NEWS README ChangeLog
%attr(755,root,root) %{_libdir}/libganglia-%{version}.so.*.*.*
%attr(755,root,root) %ghost %{_libdir}/libganglia-%{version}.so.0
%dir %{_libdir}/ganglia
%{_libdir}/ganglia/*.so
%exclude %{_libdir}/ganglia/modpython.so

%files gmetad
%defattr(644,root,root,755)
%dir %{_localstatedir}/lib/%{name}
%attr(755,ganglia,ganglia) %{_localstatedir}/lib/%{name}/rrds
%attr(755,root,root) %{_sbindir}/gmetad
%{_mandir}/man1/gmetad.1*
%attr(754,root,root) /etc/rc.d/init.d/gmetad
%dir %{_sysconfdir}/ganglia
%config(noreplace) %{_sysconfdir}/ganglia/gmetad.conf

%files gmond
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/gmetric
%attr(755,root,root) %{_bindir}/gstat
%attr(755,root,root) %{_sbindir}/gmond
%attr(754,root,root) /etc/rc.d/init.d/gmond
%{_mandir}/man5/gmond.conf.5*
%{_mandir}/man1/gmond.1*
%{_mandir}/man1/gstat.1*
%{_mandir}/man1/gmetric.1*
%dir %{_sysconfdir}/ganglia
%dir %{_sysconfdir}/ganglia/conf.d
%config(noreplace) %{_sysconfdir}/ganglia/gmond.conf
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.conf
%exclude %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files gmond-python
%defattr(644,root,root,755)
%dir %{_libdir}/ganglia/python_modules
%{_libdir}/ganglia/python_modules/*.py*
%attr(755,root,root) %{_libdir}/ganglia/modpython.so*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.pyconf*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/ganglia-config
%{_includedir}/*.h
%{_libdir}/libganglia.so

%files web
%defattr(644,root,root,755)
%doc web/AUTHORS web/COPYING
%dir %attr(750,root,http) %{_webapps}/%{_webapp}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_webapps}/%{_webapp}/apache.conf
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_webapps}/%{_webapp}/httpd.conf
%config(noreplace) %{_sysconfdir}/%{name}/conf.php
%config(noreplace) %{_sysconfdir}/%{name}/private_clusters
%{_datadir}/%{name}
