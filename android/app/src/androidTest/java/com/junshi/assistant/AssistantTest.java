package com.junshi.assistant;
import android.content.Intent;
import androidx.test.core.app.ActivityScenario;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.json.*;
import static org.junit.Assert.*;
public class AssistantTest {
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
