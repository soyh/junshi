package com.junshi.assistant;
import android.content.Intent;
import androidx.test.core.app.ActivityScenario;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.json.*;
import static org.junit.Assert.*;
public class AssistantTest {
 @Test public void compactWorkspaceKeepsTransparentBackground(){
  try(ActivityScenario<MainActivity> a=ActivityScenario.launch(MainActivity.class)){a.onActivity(activity->{Workspace workspace=new Workspace(activity);workspace.compact();assertEquals(android.graphics.Color.TRANSPARENT,((android.graphics.drawable.ColorDrawable)workspace.getBackground()).getColor());assertEquals(2,workspace.input.getMaxLines());assertEquals(3,workspace.reply.getMaxLines());});}
 }
 @Test public void captureStyledPages()throws Exception {
  try(ActivityScenario<MainActivity> a=ActivityScenario.launch(MainActivity.class)){
   InstrumentationRegistry.getInstrumentation().waitForIdleSync();capture("login");
   a.onActivity(activity->{activity.s.api=new Api("https://example.com","fake");activity.s.input="今天忙完啦，你在做什么？";activity.s.draft="刚准备休息，正好收到你的消息。今天过得怎么样？";activity.build();});
   InstrumentationRegistry.getInstrumentation().waitForIdleSync();capture("workspace");
   a.onActivity(activity->activity.s.logout());
  }
 }
 void capture(String name)throws Exception {
  android.content.Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();java.io.File dir=new java.io.File(c.getExternalFilesDir(null),"screenshots");dir.mkdirs();
  try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(dir,name+".png"))){android.graphics.Bitmap bitmap=InstrumentationRegistry.getInstrumentation().getUiAutomation().takeScreenshot();assertNotNull(bitmap);bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);bitmap.recycle();} try(android.os.ParcelFileDescriptor fd=InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand("cp "+new java.io.File(dir,name+".png").getAbsolutePath()+" /data/local/tmp/junshi-"+name+".png");java.io.InputStream in=new android.os.ParcelFileDescriptor.AutoCloseInputStream(fd)){byte[] buffer=new byte[1024];while(in.read(buffer)!=-1){}}
 }
 @Test public void receivesSharedTextAndClearsOnLogout(){
  Intent i=new Intent(InstrumentationRegistry.getInstrumentation().getTargetContext(),MainActivity.class);
  i.setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,"你在干嘛呐");
  try(ActivityScenario<MainActivity> a=ActivityScenario.launch(i)){a.onActivity(activity->{assertEquals("你在干嘛呐",activity.s.input);assertNull(activity.s.api);activity.s.logout();assertEquals("",activity.s.input);assertEquals("",activity.s.draft);});}
 }
 @Test public void retryReusesOperationAndConfirmationPayload()throws Exception {
  Api mock=new Api("https://example.com","fake"){
   String operation;int saved=0;
   @Override public Object call(String method,String path,JSONObject body)throws Exception{
    if(path.equals("/pc/messages")){if(operation==null)operation=body.getString("operation_id");else assertEquals(operation,body.getString("operation_id"));saved++;if(saved==1)throw new java.io.IOException("uncertain");return new JSONObject();}
    return Api.json("draft","刚忙完，你呢？");
   }
  };
  Session.Job job=new Session.Job("person","conversation","你好",new java.util.ArrayList<>());
  try{job.generate(mock);fail();}catch(java.io.IOException expected){}
  assertEquals("刚忙完，你呢？",job.generate(mock));
 }
}
