package com.xiaoxiao.tomato;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    /*
     * 页面从一个固定的 https 源加载，再由 WebViewClient 在本地拦截并回读 assets。
     * 这样做有两个好处：localStorage 能落在稳定的来源下（历史记录不会丢），
     * 同时页面拿到的就是正常的 https 环境，和浏览器里跑几乎没有差别。
     */
    private static final String BASE_URL = "https://tomato.local/";

    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#07080C"));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setTextZoom(100);
        if (Build.VERSION.SDK_INT >= 21) {
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (request == null || request.getUrl() == null) {
                    return null;
                }
                return serve(request.getUrl().toString());
            }
        });

        setContentView(webView);
        webView.loadUrl(BASE_URL);
    }

    /** 把 BASE_URL 下的请求映射到 assets 目录。 */
    private WebResourceResponse serve(String url) {
        if (url == null || !url.startsWith(BASE_URL)) {
            return null;
        }
        String path = url.substring(BASE_URL.length());

        int cut = path.indexOf('?');
        if (cut >= 0) {
            path = path.substring(0, cut);
        }
        cut = path.indexOf('#');
        if (cut >= 0) {
            path = path.substring(0, cut);
        }
        if (path.length() == 0) {
            path = "index.html";
        }

        String mime = path.endsWith(".js") ? "application/javascript"
                : path.endsWith(".css") ? "text/css"
                : path.endsWith(".png") ? "image/png"
                : path.endsWith(".json") ? "application/json"
                : "text/html";

        try {
            InputStream in = getAssets().open(path);
            return new WebResourceResponse(mime, "UTF-8", in);
        } catch (Exception e) {
            String msg = "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
                    + "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                    + "</head><body style=\"background:#07080C;color:#E9ECF5;"
                    + "font-family:-apple-system,sans-serif;padding:28px;line-height:1.7\">"
                    + "<h3 style=\"font-weight:600\">页面加载失败</h3>"
                    + "<p style=\"color:#8A90A6;font-size:14px\">" + path + "</p>"
                    + "<p style=\"color:#5B6073;font-size:13px\">" + e.getClass().getSimpleName()
                    + ": " + e.getMessage() + "</p></body></html>";
            return new WebResourceResponse("text/html", "UTF-8",
                    new ByteArrayInputStream(msg.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.loadUrl("about:blank");
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
