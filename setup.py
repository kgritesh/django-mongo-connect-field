from distutils.core import setup
setup(name='mongo-connect-field',
    version='0.0.1',
    packages=['mongo-connect-field'],
    license='MIT',
    author='Ritesh Kadmawala',
    author_email='ritesh@voxapp.cpm',
    description='Mongo-Connect-Field is a reusable Django field that allows you to have ForeignKey '
                'relationship between a relational model and a mongoengine document.',
    long_description=open("README.rst").read(),
)