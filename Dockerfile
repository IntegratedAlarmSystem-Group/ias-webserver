FROM centos:7

# Install oracle drivers
RUN yum install -y libaio
COPY private_files/*.rpm ./
RUN rpm -Uvh oracle-instantclient*18*.rpm
RUN if [ -d /usr/lib/oracle/18.3/client64/lib ] ; then echo "/usr/lib/oracle/18.3/client64/lib" >/etc/ld.so.conf.d/oracle-instantclient.conf ; fi
RUN if [ -d /usr/lib/oracle/18.3/client64/lib ] ; then export LD_LIBRARY_PATH=/usr/lib/oracle/18.3/client64/lib:$LD_LIBRARY_PATH ; fi
RUN if [ -d /usr/lib/oracle/18.3/client64/bin ] ; then export PATH=/usr/lib/oracle/18.3/client64/bin:$PATH ; fi
RUN ldconfig
RUN rm *.rpm

# Install python
RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm &&\
  yum -y update
RUN yum install -y gcc python36u python36u-devel python36u-pip mariadb-devel
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1 &&\
  update-alternatives --install /usr/bin/pip pip /usr/bin/pip3.6 1

# Install requirements
WORKDIR /usr/src/ias-webserver
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source files and build project
COPY . .
RUN ls -la
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

# Expose static files and port
VOLUME /usr/src/ias-webserver/static
EXPOSE 8000
