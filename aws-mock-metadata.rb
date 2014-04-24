require 'formula'

class AwsMockMetadata < Formula
    homepage 'https://github.com/dump247/aws-mock-metadata'
    head 'https://github.com/dump247/aws-mock-metadata.git'

    depends_on :python

    resource 'boto' do
        url 'https://pypi.python.org/packages/source/b/boto/boto-2.27.0.tar.gz'
        sha1 '57277486b8d4be8dda3b86739148526a9afae05d'
    end

    def install
        resource('boto').stage { system "python", "setup.py", "install", "--prefix=#{libexec}" }
    end
end
