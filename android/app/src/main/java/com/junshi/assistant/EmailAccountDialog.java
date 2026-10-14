package com.junshi.assistant;
import android.app.AlertDialog;
import android.widget.*;
import android.text.InputType;
import org.json.JSONObject;

final class EmailAccountDialog {
 static void show(MainActivity activity,boolean register){
  LinearLayout form=new LinearLayout(activity);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(24,12,24,12);
  EditText email=new EditText(activity),code=new EditText(activity),password=new EditText(activity);
  email.setHint("邮箱地址");email.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
  code.setHint("六位验证码（10 分钟有效）");code.setInputType(InputType.TYPE_CLASS_NUMBER);
  password.setHint("密码 12–256 字符");password.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
  Theme.background(form);Theme.input(email);Theme.input(password);Theme.input(code);
  form.addView(email);form.addView(password);form.addView(code);TextView status=Theme.label(form,"",14);
  LinearLayout actions=new LinearLayout(activity);form.addView(actions);
  Button send=new Button(activity),submit=new Button(activity);send.setText("发送验证码");submit.setText(register?"确认注册":"重置密码");Theme.button(send,false);Theme.button(submit,true);actions.addView(send);actions.addView(submit);
  String base=activity.server.getText().toString(),name=activity.user.getText().toString(),purpose=register?"register":"reset";
  final String[] challenge={null,null};
  AlertDialog dialog=new AlertDialog.Builder(activity).setTitle(register?"邮箱验证注册":"邮箱找回密码").setView(form).setNegativeButton("关闭",null).create();
  Runnable listener=()->{if(dialog.isShowing()){status.setText(activity.s.status);send.setEnabled(!activity.s.busy);submit.setEnabled(!activity.s.busy);}};activity.s.listen(listener);
  dialog.setOnDismissListener(d->{activity.s.unlisten(listener);password.setText("");code.setText("");challenge[0]=null;challenge[1]=null;});
  send.setOnClickListener(v->{if(activity.s.busy)return;String address=email.getText().toString().trim();send.setEnabled(false);status.setText("正在发送…");activity.s.run("正在发送验证码…",()->new Api(base,null).object("POST","/auth/email/code",Api.json("email",address,"purpose",purpose)),r->{if(!dialog.isShowing())return;challenge[0]=r.optString("challenge_id");challenge[1]=address;status.setText(r.optString("message"));send.setEnabled(true);});});
  submit.setOnClickListener(v->{if(activity.s.busy)return;String address=email.getText().toString().trim(),pass=password.getText().toString();String error=RegistrationRules.error(register?name:"reset-user",pass);if(error!=null){status.setText(error);return;}if(challenge[0]==null||!address.equals(challenge[1])){status.setText("请先发送验证码");return;}String id=challenge[0],value=code.getText().toString();activity.s.run("正在验证…",()->{Api api=new Api(base,null);JSONObject p=Api.json("email",address,"challenge_id",id,"code",value);if(register){p.put("username",name);p.put("password",pass);}else p.put("new_password",pass);JSONObject result=api.object("POST",register?"/auth/email/register":"/auth/email/reset-password",p);if(register&&result.optString("access_token").isEmpty())throw new java.io.IOException("服务器未返回登录状态，请核对账号后重新登录");return result;},r->{if(register){activity.s.api=new Api(base,r.optString("access_token"));activity.password.setText("");activity.getPreferences(0).edit().putString("server",base).apply();activity.build();activity.s.loadPeople();}else activity.s.message("密码已重置，请重新登录");dialog.dismiss();});});
  dialog.show();
 }
 private EmailAccountDialog(){}
}
