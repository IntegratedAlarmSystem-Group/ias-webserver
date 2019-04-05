FROM centos:7

# Install oracle drivers (Important: before python installation)
RUN yum install -y libaio
COPY private_files/*.rpm ./
RUN if [ -f oracle-instantclient18.3-basic-18.3.0.0.0-1.x86_64.rpm ] ; then rpm -Uvh oracle-instantclient*18*.rpm ; fi
RUN if [ -d /usr/lib/oracle/18.3/client64/lib ] ; then echo "/usr/lib/oracle/18.3/client64/lib" >/etc/ld.so.conf.d/oracle-instantclient.conf ; fi
RUN if [ -d /usr/lib/oracle/18.3/client64/lib ] ; then export LD_LIBRARY_PATH=/usr/lib/oracle/18.3/client64/lib:$LD_LIBRARY_PATH ; fi
RUN if [ -d /usr/lib/oracle/18.3/client64/bin ] ; then export PATH=/usr/lib/oracle/18.3/client64/bin:$PATH ; fi
RUN if [ -f oracle-instantclient18.3-basic-18.3.0.0.0-1.x86_64.rpm ]; then rm *.rpm ; fi
RUN ldconfig

# Install netcat
RUN yum update -y && yum install -y nmap-ncat

# Install python
RUN yum install -y gcc openssl-devel bzip2-devel libffi-devel wget make
RUN yum install -y mysql-devel sqlite-devel
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
RUN tar xzf Python-3.7.3.tgz
WORKDIR /usr/src/Python-3.7.3
RUN ./configure --enable-optimizations
RUN make install
RUN rm -rf /usr/src/Python-3.7.3
RUN rm -rf /usr/src/Python-3.7.3.tgz
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3.7 1 &&\
  update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.7 1

# Install requirements
WORKDIR /usr/src/ias-webserver
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source files and build project
COPY . .
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

RUN python manage.py collectstatic --noinput

# Expose static files and port
VOLUME /usr/src/ias-webserver/static
EXPOSE 8000
