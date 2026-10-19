# Nova: keep OkHttp/Media3 public APIs (their own consumer rules cover most of this).
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class androidx.media3.** { *; }
