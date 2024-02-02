# syntax = docker/dockerfile:1.4
FROM hub.opensciencegrid.org/opensciencegrid/software-base:23-el9-release

RUN curl --output /etc/yum.repos.d/pegasus.repo \
         https://download.pegasus.isi.edu/pegasus/rhel/9/pegasus.repo
RUN dnf install -y epel-release

RUN dnf install -y \
        apptainer \
        condor \
        pegasus \
        mesa-libGL \
        python3-pip

RUN dnf install -y https://download.pegasus.isi.edu/pegasus/5.0.7dev/pegasus-5.0.7dev-1.el9.x86_64.rpm

RUN ls -l /usr/lib64/python3.9/site-packages/Pegasus/cli/pegasus-config.py && \
    chmod 644 /usr/lib64/python3.9/site-packages/Pegasus/cli/pegasus-config.py

RUN python3 -m pip install fastapi[all]

# install pywaggle
RUN pip3 install --no-cache-dir git+https://github.com/waggle-sensor/pywaggle
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN useradd pegasus

COPY config/50-main.config /etc/condor/config.d/

COPY config/10-setup.sh /etc/osg/image-init.d

COPY pegasus-wrapper /opt/pegasus-wrapper
RUN chmod 755 /opt/pegasus-wrapper

# sage workflow
COPY workflow /home/pegasus/workflow
RUN chown -R pegasus: /home/pegasus/workflow
RUN chmod 755 -R /home/pegasus/workflow/executables

# copy entrypoint
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod 755 /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
