from setuptools import setup, find_packages

if __name__ == '__main__':
    package_name = 'bettertutors_aws_scripts'
    setup(
        name=package_name,
        author='Samuel Marks',
        version='0.3.0',
        test_suite='test',
        packages=filter(lambda p: p != 'test', find_packages()),  # exclude='test' doesn't work
        package_data={package_name: ['logging.conf']},
        install_requires=[
            'boto3', 'fabric',
            'boto'  # TODO: Remove this dependency
        ]
    )
