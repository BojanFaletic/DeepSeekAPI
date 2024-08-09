FROM ubuntu:latest

RUN apt-get update && apt-get install -y openssh-server python3 python3-numpy
RUN mkdir /var/run/sshd /mnt/tempfs

RUN useradd -m python && echo "python:python" | chpasswd
RUN chown python:python /mnt/tempfs

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]