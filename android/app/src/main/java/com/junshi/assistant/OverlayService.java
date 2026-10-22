package com.junshi.assistant;
import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.PixelFormat;
import android.provider.Settings;
import android.view.*;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
public class OverlayService extends Service {
 WindowManager wm;View view;WindowManager.LayoutParams params;boolean expanded;boolean typing;
 @Override public IBinder onBind(Intent i){return null;}
 @Override public int onStartCommand(Intent i,int flags,int id){if(i!=null&&"stop".equals(i.getAction())){stopSelf();return START_NOT_STICKY;}if(!Settings.canDrawOverlays(this)||((Session)getApplication()).api==null){stopSelf();return START_NOT_STICKY;}NotificationManager nm=getSystemService(NotificationManager.class);nm.createNotificationChannel(new NotificationChannel("assistant","悬浮助手",NotificationManager.IMPORTANCE_LOW));PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,OverlayService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE);startForeground(222,new Notification.Builder(this,"assistant").setSmallIcon(com.junshi.assistant.R.drawable.ic_assistant).setContentTitle("AI 恋爱军师悬浮助手").setContentText("点击气泡展开；可随时关闭").setContentIntent(open).addAction(new Notification.Action.Builder(null,"关闭",stop).build()).build());if(view==null){wm=getSystemService(WindowManager.class);show(false);}return START_NOT_STICKY;}
 void show(boolean large){if(view!=null)wm.removeView(view);expanded=large;typing=false;int width=large?Math.min((int)(getResources().getDisplayMetrics().widthPixels*0.82f),dp(304)):dp(56);
  // 小窗默认不抢输入焦点、也不吃键盘：下面的应用（微信等）照常能弹出输入法。
  // 只有点了「输入」才临时变成可聚焦窗口，收起键盘后再还回去。
  int flags=WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;
  if(large)flags|=WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL;
  params=new WindowManager.LayoutParams(width,WindowManager.LayoutParams.WRAP_CONTENT,WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,flags,PixelFormat.TRANSLUCENT);params.gravity=Gravity.TOP|Gravity.START;params.x=dp(12);params.y=dp(60);params.dimAmount=0f;params.flags &= ~WindowManager.LayoutParams.FLAG_DIM_BEHIND;params.softInputMode=WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;
 LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setBackgroundColor(android.graphics.Color.TRANSPARENT);box.setPadding(dp(2),dp(2),dp(2),dp(2));Button header=new Button(this);header.setText(large?"拖动移动 · 点击收起":"军师");box.addView(header);Theme.button(header,true);header.setLayoutParams(new LinearLayout.LayoutParams(-1,dp(48)));header.setOnClickListener(v->show(!expanded));header.setOnTouchListener(new View.OnTouchListener(){float x,y;int px,py;boolean moved;public boolean onTouch(View v,android.view.MotionEvent e){if(e.getAction()==0){x=e.getRawX();y=e.getRawY();px=params.x;py=params.y;moved=false;}else if(e.getAction()==2){float dx=e.getRawX()-x,dy=e.getRawY()-y;if(Math.abs(dx)+Math.abs(dy)>12)moved=true;params.x=Math.max(0,px+(int)dx);params.y=Math.max(0,py+(int)dy);wm.updateViewLayout(view,params);}else if(e.getAction()==1&&moved)return true;return false;}});
 if(large){ScrollView scroll=new ScrollView(this);Workspace workspace=new Workspace(this);workspace.compact();scroll.addView(workspace);scroll.setFillViewport(false);scroll.setBackgroundColor(android.graphics.Color.TRANSPARENT);box.addView(scroll,new LinearLayout.LayoutParams(-1,Math.min((int)(getResources().getDisplayMetrics().heightPixels*0.48f),dp(320))));LinearLayout footer=new LinearLayout(this);box.addView(footer);Workspace.button(footer,"输入",()->setTyping(true));Workspace.button(footer,"收起键盘",this::releaseKeyboard);Workspace.button(footer,"打开 App",()->{startActivity(new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));show(false);});Workspace.button(footer,"关闭",this::stopSelf);}
 view=box;wm.addView(view,params);}
 /** 临时把窗口变成可聚焦，让键盘能落到小窗里的输入框。 */
 void setTyping(boolean on){if(view==null||params==null)return;typing=on;try{if(on)params.flags &= ~WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;else params.flags |= WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;wm.updateViewLayout(view,params);}catch(Exception ignored){return;}if(on){view.setFocusableInTouchMode(true);view.postDelayed(() -> {EditText target=findEditor(view);if(target!=null){target.requestFocus();InputMethodManager imm=(InputMethodManager)getSystemService(INPUT_METHOD_SERVICE);if(imm!=null)imm.showSoftInput(target,InputMethodManager.SHOW_IMPLICIT);}},80);}else releaseKeyboard();}
 /** 收起键盘，并把输入焦点还给下面的应用。 */
 void releaseKeyboard(){if(view==null||params==null)return;typing=false;try{InputMethodManager imm=(InputMethodManager)getSystemService(INPUT_METHOD_SERVICE);if(imm!=null)imm.hideSoftInputFromWindow(view.getWindowToken(),0);View focused=view.findFocus();if(focused!=null)focused.clearFocus();params.flags |= WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;wm.updateViewLayout(view,params);}catch(Exception ignored){}}
 EditText findEditor(View root){if(root instanceof EditText)return (EditText)root;if(root instanceof ViewGroup){ViewGroup group=(ViewGroup)root;for(int i=0;i<group.getChildCount();i++){EditText found=findEditor(group.getChildAt(i));if(found!=null)return found;}}return null;}
 int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
 @Override public void onDestroy(){if(view!=null&&wm!=null)wm.removeView(view);view=null;super.onDestroy();}
}
