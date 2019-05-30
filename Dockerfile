FROM nvidia/cuda:10.1-devel

ENV BEAST_VERSION 1.10.4
ENV PATH="$PATH:/opt/beast/bin"
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/lib"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential autoconf automake libtool git pkg-config openjdk-8-jdk openjdk-8-jre python curl python-setuptools
RUN git clone --depth=1 https://github.com/beagle-dev/beagle-lib.git \
    && cd beagle-lib \
    && ./autogen.sh \
    && ./configure --prefix=/usr \
    && make install
RUN curl -L https://github.com/beast-dev/beast-mcmc/releases/download/v${BEAST_VERSION}/BEASTv${BEAST_VERSION}.tgz | tar xzvf - \
    && mv BEASTv${BEAST_VERSION} /opt/beast
RUN git clone https://github.com/necrolyte2/beast_whip.git \
    && cd beast_whip \
    && python setup.py install
