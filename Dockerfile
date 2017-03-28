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
FROM centos:latest
RUN yum -y update ;
RUN yum clean all ;
RUN yum install -y epel-release ;
RUN yum install -y ansible git gcc gcc-c++ make net-tools sudo which wget file patch libtool texinfo tar unzip bzip2 bzip2-devel ; 
RUN yum install -y openssl openssl-devel readline readline-devel sqlite-devel tk-devel zlib zlib-devel ncurses-devel python-pip mc ;
RUN yum clean all ;

##############################################################
# Dockerfile Version:   1.0
# Software:             ChIps
# Software Version:     1.0
# Software Website:     
# Description:          ChIps python workflow
##############################################################

RUN wget https://raw.githubusercontent.com/amirshams84/Chips/master/chips.py -P $CURRENT_PATH

CMD ["/bin/bash"]
