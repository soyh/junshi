package com.junshi.assistant;
import android.app.Activity;
import android.app.AlertDialog;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.webkit.*;
public class WebActivity extends Activity {
 static final int LOCATION_REQUEST = 41;
 WebView web;
 GeolocationPermissions.Callback pendingLocation;
 String pendingOrigin;
 @Override public void onCreate(Bundle b){super.onCreate(b);String origin=getIntent().getStringExtra("origin"),ticket=getIntent().getStringExtra("ticket");try{origin=UrlPolicy.base(origin);if(ticket==null||!ticket.matches("[A-Za-z0-9_-]{43}"))throw new IllegalArgumentException();}catch(Exception e){finish();return;}final String trusted=origin;web=new WebView(this);
  WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setGeolocationEnabled(true);
  web.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !UrlPolicy.sameOrigin(trusted,r.getUrl().toString());}});
  // 没有 WebChromeClient 时，页面里的 alert / confirm / prompt 全部无声失败——
  // 手机上「修改消息」这类按钮就看起来点了没反应。
  web.setWebChromeClient(new WebChromeClient(){
   @Override public boolean onJsAlert(WebView v,String url,String message,JsResult result){new AlertDialog.Builder(WebActivity.this).setMessage(message).setPositiveButton("好",(d,w)->result.confirm()).setOnCancelListener(d->result.cancel()).show();return true;}
   @Override public boolean onJsConfirm(WebView v,String url,String message,JsResult result){new AlertDialog.Builder(WebActivity.this).setMessage(message).setPositiveButton("确定",(d,w)->result.confirm()).setNegativeButton("取消",(d,w)->result.cancel()).setOnCancelListener(d->result.cancel()).show();return true;}
   @Override public boolean onJsPrompt(WebView v,String url,String message,String defaultValue,JsPromptResult result){final android.widget.EditText input=new android.widget.EditText(WebActivity.this);input.setText(defaultValue==null?"":defaultValue);input.setSelection(input.getText().length());new AlertDialog.Builder(WebActivity.this).setMessage(message).setView(input).setPositiveButton("确定",(d,w)->result.confirm(input.getText().toString())).setNegativeButton("取消",(d,w)->result.cancel()).setOnCancelListener(d->result.cancel()).show();return true;}
   @Override public void onGeolocationPermissionsShowPrompt(String origin,GeolocationPermissions.Callback callback){
    if(Build.VERSION.SDK_INT>=23&&checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED){pendingLocation=callback;pendingOrigin=origin;requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},LOCATION_REQUEST);return;}
    callback.invoke(origin,true,false);
   }
  });
  setContentView(web);web.loadUrl(origin+"/app#desktop-login="+ticket);getIntent().removeExtra("ticket");}
 @Override public void onRequestPermissionsResult(int code,String[] permissions,int[] results){super.onRequestPermissionsResult(code,permissions,results);if(code!=LOCATION_REQUEST)return;boolean granted=results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED;if(pendingLocation!=null)pendingLocation.invoke(pendingOrigin,granted,false);pendingLocation=null;pendingOrigin=null;}
 @Override protected void onDestroy(){if(web!=null){web.stopLoading();web.destroy();}super.onDestroy();}
}
