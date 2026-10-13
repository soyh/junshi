package com.junshi.assistant;
import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.PixelFormat;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
public class OverlayService extends Service {
 WindowManager wm;View view;WindowManager.LayoutParams params;boolean expanded;
 @Override public IBinder onBind(Intent i){return null;}
 @Override public int onStartCommand(Intent i,int flags,int id){if(i!=null&&"stop".equals(i.getAction())){stopSelf();return START_NOT_STICKY;}if(!Settings.canDrawOverlays(this)||((Session)getApplication()).api==null){stopSelf();return START_NOT_STICKY;}NotificationManager nm=getSystemService(NotificationManager.class);nm.createNotificationChannel(new NotificationChannel("assistant","悬浮助手",NotificationManager.IMPORTANCE_LOW));PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,OverlayService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE);startForeground(222,new Notification.Builder(this,"assistant").setSmallIcon(com.junshi.assistant.R.drawable.ic_assistant).setContentTitle("AI 恋爱军师悬浮助手").setContentText("点击气泡展开；可随时关闭").setContentIntent(open).addAction(new Notification.Action.Builder(null,"关闭",stop).build()).build());if(view==null){wm=getSystemService(WindowManager.class);show(false);}return START_NOT_STICKY;}
 void show(boolean large){if(view!=null)wm.removeView(view);expanded=large;int width=large?Math.min(getResources().getDisplayMetrics().widthPixels-24,480):64;params=new WindowManager.LayoutParams(width,WindowManager.LayoutParams.WRAP_CONTENT,WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,large?WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL:WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,PixelFormat.TRANSLUCENT);params.gravity=Gravity.TOP|Gravity.START;params.x=12;params.y=100;
 LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setBackgroundColor(0xfff1f8ff);Button header=new Button(this);header.setText(large?"拖动移动 · 点击收起":"军师");box.addView(header);header.setOnClickListener(v->show(!expanded));header.setOnTouchListener(new View.OnTouchListener(){float x,y;int px,py;boolean moved;public boolean onTouch(View v,android.view.MotionEvent e){if(e.getAction()==0){x=e.getRawX();y=e.getRawY();px=params.x;py=params.y;moved=false;}else if(e.getAction()==2){float dx=e.getRawX()-x,dy=e.getRawY()-y;if(Math.abs(dx)+Math.abs(dy)>12)moved=true;params.x=Math.max(0,px+(int)dx);params.y=Math.max(0,py+(int)dy);wm.updateViewLayout(view,params);}else if(e.getAction()==1&&moved)return true;return false;}});
 if(large){ScrollView scroll=new ScrollView(this);scroll.addView(new Workspace(this));box.addView(scroll,new LinearLayout.LayoutParams(-1,Math.min(getResources().getDisplayMetrics().heightPixels-220,700)));LinearLayout footer=new LinearLayout(this);box.addView(footer);Workspace.button(footer,"打开 App / 添加附件",()->{startActivity(new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));show(false);});Workspace.button(footer,"关闭",this::stopSelf);}view=box;wm.addView(view,params);}
 @Override public void onDestroy(){if(view!=null&&wm!=null)wm.removeView(view);view=null;super.onDestroy();}
}
