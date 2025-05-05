from setuptools import setup, find_packages
import os

# README 파일 읽기
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()

setup(
    name='EventLogAnalyzer',
    version='0.2.0', # 버전 업데이트
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pywin32;platform_system=="Windows"',
        'rich>=13.0.0',
        'python-dotenv>=1.0.0', # 추가
        'requests>=2.28.0',     # 추가
    ],
    entry_points={
        'console_scripts': [
            # src 패키지 내 main 모듈의 run_analyzer 함수를 실행하는 명령어 'analyze-logs' 생성
            'analyze-logs = main:run_analyzer',
        ],
    },
    author='[Your Name]', # !수정필요! 작성자 이름
    author_email='[Your Email]', # !수정필요! 작성자 이메일
    description='Windows Event Log Analyzer using LLM',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/[Your GitHub Username]/EventLogAnalyzer', # !수정필요! 프로젝트 URL
    license='MIT', # 라이선스 명시
    classifiers=[
        'Development Status :: 3 - Alpha', # 개발 상태
        'Intended Audience :: System Administrators',
        'Topic :: System :: Logging',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    keywords='windows event log analyzer llm groq troubleshooting', # 검색 키워드
)