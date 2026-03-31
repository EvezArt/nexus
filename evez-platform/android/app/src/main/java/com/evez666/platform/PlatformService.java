package com.evez666.platform;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;

import java.util.Locale;

public class PlatformService extends Service implements TextToSpeech.OnInitListener {

    private static final String CHANNEL_ID = "evez_platform";
    private static final int NOTIFICATION_ID = 1;
    private TextToSpeech tts;
    private boolean ttsReady = false;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        startForeground(NOTIFICATION_ID, buildNotification("EVEZ666 running"));

        // Initialize TTS
        tts = new TextToSpeech(this, this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Handle speak commands from WebView
        if (intent != null && "SPEAK".equals(intent.getAction())) {
            String text = intent.getStringExtra("text");
            if (text != null && ttsReady) {
                speak(text);
            }
        }
        return START_STICKY;
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            tts.setLanguage(Locale.US);
            tts.setSpeechRate(1.0f);
            tts.setPitch(1.0f);
            ttsReady = true;

            tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override
                public void onStart(String utteranceId) {}
                @Override
                public void onDone(String utteranceId) {}
                @Override
                public void onError(String utteranceId) {}
            });
        }
    }

    public void speak(String text) {
        if (tts != null && ttsReady) {
            tts.speak(text, TextToSpeech.QUEUE_ADD, null, "evez_speak_" + System.currentTimeMillis());
        }
    }

    public void stopSpeaking() {
        if (tts != null) {
            tts.stop();
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "EVEZ Platform", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("EVEZ666 cognitive platform background service");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(channel);
        }
    }

    private Notification buildNotification(String text) {
        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }
        return builder
            .setContentTitle("EVEZ666")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .build();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
