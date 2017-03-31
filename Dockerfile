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
RUN yum install -y tbb psmisc ;
RUN yum clean all ;
##############################################################
# Software:             PIP INSTALL PACKAGES
# Software Version:     1.0
# Software Website:     -
# Description:          required javascript library
##############################################################
ENTRYPOINT ["/bin/bash"]
RUN pip install --upgrade pip
RUN pip install numpy
RUN pip install scipy
RUN pip install plotly
RUN pip install pandas
#RUN pip install biom-format
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
RUN mkdir /INPUTDIR /EXECDIR /OUTPUTDIR /TESTDIR /INDEXDIR
RUN chmod -R 0755 /INPUTDIR /EXECDIR /OUTPUTDIR /TESTDIR /INDEXDIR

##############################################################
# Dockerfile Version:   1.0
# Software:             mothur
# Software Version:     1.39
# Software Website:     www.mothur.org
# Description:          mothur 
##############################################################
 
RUN wget https://github.com/mothur/mothur/releases/download/v1.39.5/Mothur.linux_64.zip -P /EXECDIR
RUN unzip /EXECDIR/Mothur.linux_64.zip -d /EXECDIR
RUN rm -rf /EXECDIR/Mothur.linux_64.zip /EXECDIR/__MACOSX
RUN chmod -R 0755 /EXECDIR/mothur

##############################################################
# Dockerfile Version:   1.0
# Software:             bowtie
# Software Version:     1.2
# Software Website:     bowtie
# Description:          bowtie 
##############################################################

RUN mkdir /EXECDIR/bowtie
RUN wget https://sourceforge.net/projects/bowtie-bio/files/bowtie/1.2.0/bowtie-1.2-linux-x86_64.zip -P /EXECDIR/bowtie
RUN unzip /EXECDIR/bowtie/bowtie-1.2-linux-x86_64.zip -d /EXECDIR/bowtie
RUN rm -rf /EXECDIR/bowtie/bowtie-1.2-linux-x86_64.zip
RUN chmod -R 0755 /EXECDIR/bowtie/bowtie-1.2


##############################################################
# Dockerfile Version:   1.0
# Software:             SAMTOOLS
# Software Version:     1.4.2
# Software Website:     SAMTOOLS
# Description:          SAMTOOLS 
##############################################################

RUN mkdir /EXECDIR/samtools
RUN wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2 -P /EXECDIR/samtools
RUN tar xvjf /EXECDIR/samtools/samtools-1.3.1.tar.bz2 -C /EXECDIR/samtools
RUN rm -rf /EXECDIR/samtools/samtools-1.3.1.tar.bz2
RUN chmod -R 0755 /EXECDIR/samtools/samtools-1.3.1
WORKDIR /EXECDIR/samtools/samtools-1.3.1
RUN make
RUN make prefix=. install

##############################################################
# Dockerfile Version:   1.0
# Software:             MACS
# Software Version:     1.4.2
# Software Website:     MACS
# Description:          MACS 
##############################################################

RUN mkdir/EXECDIR/macs
RUN wget wget https://github.com/downloads/taoliu/MACS/MACS-1.4.2-1.tar.gz -P /EXECDIR/macs
RUN tar zxvf /EXECDIR/macs/MACS-1.4.2-1.tar.gz -C /EXECDIR/macs
RUN rm -rf /EXECDIR/macs/MACS-1.4.2-1.tar.gz
RUN chmod -R 0755 /EXECDIR/macs/MACS-1.4.2
WORKDIR /EXECDIR/macs/MACS-1.4.2
RUN python setup.py install --user

##############################################################
# Dockerfile Version:   1.0
# Software:             ChIps
# Software Version:     1.0
# Software Website:     
# Description:          ChIps python workflow
##############################################################
WORKDIR /
RUN wget https://raw.githubusercontent.com/amirshams84/Chips/master/chips.py -P /

ENTRYPOINT ["/bin/bash"]
