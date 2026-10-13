package com.junshi.assistant;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.*;
public class WebActivity extends Activity {
 WebView web;
 @Override public void onCreate(Bundle b){super.onCreate(b);String origin=getIntent().getStringExtra("origin"),ticket=getIntent().getStringExtra("ticket");try{origin=UrlPolicy.base(origin);if(ticket==null||!ticket.matches("[A-Za-z0-9_-]{43}"))throw new IllegalArgumentException();}catch(Exception e){finish();return;}final String trusted=origin;web=new WebView(this);web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);web.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !UrlPolicy.sameOrigin(trusted,r.getUrl().toString());}});setContentView(web);web.loadUrl(origin+"/app#desktop-login="+ticket);getIntent().removeExtra("ticket");}
 @Override protected void onDestroy(){if(web!=null){web.stopLoading();web.destroy();}super.onDestroy();}
}
