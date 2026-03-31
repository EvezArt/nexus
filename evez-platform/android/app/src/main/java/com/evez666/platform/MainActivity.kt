package com.evez666.platform

import android.app.*
import android.content.*
import android.os.*
import android.webkit.*
import android.net.http.SslError
import android.graphics.Color
import android.view.View
import androidx.core.app.NotificationCompat

/**
 * EVEZ666 — Native Android App
 * WebView wrapper + embedded Python server via Termux/Chaquopy
 * Targets Android 16 (API 36)
 */
class MainActivity : Activity() {

    private lateinit var webView: WebView
    private var serverPort = 8080

    companion object {
        const val CHANNEL_ID = "evez666_platform"
        const val NOTIFICATION_ID = 1
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Create notification channel for background service
        createNotificationChannel()

        // Start embedded server
        startPlatformServer()

        // Setup WebView
        webView = WebView(this)
        setContentView(webView)

        webView.apply {
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                databaseEnabled = true
                allowFileAccess = true
                allowContentAccess = true
                mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                mediaPlaybackRequiresUserGesture = false
                userAgentString = "EVEZ666/0.2.0 Android/16"
                cacheMode = WebSettings.LOAD_DEFAULT
                setSupportZoom(false)
            }

            // Enable WebView debugging in debug builds
            WebView.setWebContentsDebuggingEnabled(true)

            // Chrome client for full web compat
            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    request?.grant(request.resources)
                }
            }

            // Allow all SSL (for local dev — production should use proper certs)
            webViewClient = object : WebViewClient() {
                override fun onReceivedSslError(view: WebView?, handler: SslErrorHandler?, error: SslError?) {
                    handler?.proceed()
                }
            }

            // Load EVEZ platform
            loadUrl("http://localhost:$serverPort")
        }

        // Show foreground notification
        startForegroundNotification()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "EVEZ666 Platform",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "EVEZ666 cognitive platform running"
                lightColor = Color.parseColor("#6366f1")
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun startForegroundNotification() {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("⚡ EVEZ666")
            .setContentText("Cognitive platform active")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun startPlatformServer() {
        // Launch embedded Python server via native process
        // On Android, this runs via Termux or embedded Python
        Thread {
            try {
                val process = Runtime.getRuntime().exec(
                    arrayOf("python3", "main.py"),
                    arrayOf("EVEZ_PORT=$serverPort"),
                    filesDir
                )
                process.waitFor()
            } catch (e: Exception) {
                // Fallback: server may be running via Termux
                // WebView will connect to localhost:8080
            }
        }.start()
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}
