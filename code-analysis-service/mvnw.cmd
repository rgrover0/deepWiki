@REM ----------------------------------------------------------------------------
@REM Maven Wrapper startup batch script
@REM Auto-downloads Apache Maven 3.9.6 on first run via HTTPS
@REM ----------------------------------------------------------------------------
@IF "%__MVNW_ARG0_NAME__%"=="" (SET "__MVNW_ARG0_NAME__=%~nx0")
@SET __ MAVEN_PROJECTBASEDIR=%~dp0

@SET MAVEN_WRAPPER_JAR="%~dp0.mvn\wrapper\maven-wrapper.jar"
@SET MAVEN_WRAPPER_PROPERTIES="%~dp0.mvn\wrapper\maven-wrapper.properties"
@SET DOWNLOAD_URL=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.3.2/maven-wrapper-3.3.2.jar

@FOR /F "usebackq tokens=1,2 delims==" %%A IN (%MAVEN_WRAPPER_PROPERTIES%) DO (
    @IF "%%A"=="distributionUrl" SET DISTRIBUTION_URL=%%B
)

@IF NOT EXIST %MAVEN_WRAPPER_JAR% (
    @echo Downloading maven-wrapper.jar ...
    @powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile %MAVEN_WRAPPER_JAR%"
)

@IF NOT "%JAVA_HOME%"=="" GOTO javaHomeSet
@FOR %%j IN (java.exe) DO @SET "JAVA_EXE=%%~$PATH:j"
@IF NOT "%JAVA_EXE%"=="" GOTO javaExeSet
@echo Error: JAVA_HOME not set and java not found in PATH. >&2
@exit /B 1
:javaHomeSet
@SET "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
:javaExeSet

@SET MAVEN_OPTS=%MAVEN_OPTS% -Dmaven.multiModuleProjectDirectory=%~dp0
@"%JAVA_EXE%" %JVM_CONFIG_MAVEN_PROPS% %MAVEN_OPTS% %MAVEN_DEBUG_OPTS% ^
  -classpath %MAVEN_WRAPPER_JAR% ^
  "-Dmaven.multiModuleProjectDirectory=%~dp0" ^
  org.apache.maven.wrapper.MavenWrapperMain %* %MAVEN_CONFIG%
