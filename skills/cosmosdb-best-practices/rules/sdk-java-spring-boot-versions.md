---
title: Spring Boot and Java version compatibility for Cosmos DB SDK
impact: CRITICAL
impactDescription: Prevents build failures due to version incompatibility between Spring Boot and Java
tags: java, spring-boot, sdk, version-requirements, compatibility
---

## Spring Boot and Java version compatibility for Cosmos DB SDK

## Spring Boot and Java Version Requirements

The Azure Cosmos DB Java SDK works with various Spring Boot versions, but each Spring Boot version has **strict Java version requirements** that must be met for the project to build successfully.

**Incorrect:**

```
[ERROR] bad class file...has wrong version 61.0, should be 55.0
[ERROR] release version 17 not supported
```

**Correct:**


```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.1</version>
</parent>

<properties>
    <java.version>17</java.version>
```

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>

<properties>
    <java.version>11</java.version>  <!-- or 17 -->
```
