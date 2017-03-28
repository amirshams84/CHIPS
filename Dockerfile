FROM centos:latest
MAINTAINER Amir Shams <amir.shams84@gmail.com>
ENV ROOT=/
ENV CURRENT_PATH=/
##############################################################
# Dockerfile Version:   1.0
# Software:             centos7
# Software Version:     7.0
# Software Website:     https://www.centos.org/
# Description:          Centos7
##############################################################

RUN yum -y update ;
RUN yum clean all ;
RUN yum install -y epel-release ;
RUN yum install -y ansible git gcc gcc-c++ make net-tools sudo which wget file patch libtool texinfo tar unzip bzip2 bzip2-devel ; 
RUN yum install -y openssl openssl-devel readline readline-devel sqlite-devel tk-devel zlib zlib-devel ncurses-devel python-pip mc ;
RUN yum clean all ;

CMD ["/bin/bash"]
RUN mkdir /ChIps_EXECDIR
RUN mkdir /ChIps_OUTPUTDIR
RUN mkdir /ChIps_TESTDIR
##############################################################
# Dockerfile Version:   1.0
# Software:             mothur
# Software Version:     1.39
# Software Website:     www.mothur.org
# Description:          mothur 
##############################################################

RUN wget https://github.com/mothur/mothur/releases/download/v1.39.5/Mothur.linux_64.zip -P /ChIps_EXECDIR
RUN unzip /ChIps_EXECDIR/Mothur.linux_64.zip -d /ChIps_EXECDIR
RUN rm -rf /ChIps_EXECDIR/Mothur.linux_64.zip /ChIps_EXECDIR/__MACOSX
RUN chmod -R 0755 /ChIps_EXECDIR/mothur

##############################################################
# Dockerfile Version:   1.0
# Software:             ChIps
# Software Version:     1.0
# Software Website:     
# Description:          ChIps python workflow
##############################################################

RUN wget https://raw.githubusercontent.com/amirshams84/Chips/master/chips.py -P /

CMD ["/bin/bash"]
