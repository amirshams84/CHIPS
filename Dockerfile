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
##############################################################
# Software:             PIP INSTALL PACKAGES
# Software Version:     1.0
# Software Website:     -
# Description:          required javascript library
##############################################################
RUN pip install numpy
RUN pip install scipy
RUN pip install plotly
RUN pip install pandas
RUN pip install biom-format
RUN pip install xlrd
RUN pip install openpyxl
RUN pip install xlwt
RUN pip install XlsxWriter
RUN pip install lxml
RUN pip install zip
##############################################################
# Software:             Regular
# Software Version:     1.0
# Software Website:     -
# Description:          required javascript library
##############################################################

ENTRYPOINT ["/bin/bash"]
RUN mkdir /ChIps_EXECDIR /ChIps_OUTPUTDIR /ChIps_TESTDIR
RUN chmod -R 0755 /ChIps_EXECDIR /ChIps_OUTPUTDIR /ChIps_TESTDIR
# create bind points for NIH HPC environment
RUN mkdir /gpfs /spin1 /gs2 /gs3 /gs4 /gs5 /gs6 /data /scratch /fdb /lscratch
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

ENTRYPOINT ["/bin/bash"]
