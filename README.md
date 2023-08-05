# LibScanner

- LibScanner is an automatic tool for Android library detection.
- Upload your apk file and LibRadar can detect third-party libraries in Android apps accurately and instantly，even after code shrinking(dead code removal).

## Introduction
This is a tool designed to detect third-party libraries in Android applications, even after code shrinking. It helps developers quickly identify the third-party libraries used in their Android projects, along with their version information, licenses, and other relevant details. With this tool, you can better manage and maintain your Android projects.

## Key Features
- List all third-party libraries used in the application, including version information.
- Provide license information for each third-party library.

## Require
download this project and prepare python environment.
- Android SDK
- python 3.8
- androguard 3.4.0
- pyssdeep
- mysql 8.0.23

## Install
You can install this tool using one of the following methods:

- Download the latest release and add it to your project.
- Clone this repository and integrate the tool into your project.

## Usage Example
```
$ python LibScanner/LibScanner.py example.apk
```


