package com.junshi.assistant;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.view.View;
import android.widget.*;

/** Shared blue-white surfaces for the activity and overlay. */
final class Theme {
 static final int BLUE=0xff287bc1, INK=0xff23415b, MUTED=0xff607b91, BG=0xffedf5fc;
 static int dp(Context c,int n){return Math.round(n*c.getResources().getDisplayMetrics().density);}
 static GradientDrawable surface(Context c,int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(c,radius));g.setStroke(dp(c,1),0xffd7e6f3);return g;}
 static void background(View v){GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{0xffe7f3ff,0xfff8fbff,0xffeef6fc});v.setBackground(g);}
 static TextView label(LinearLayout parent,String text,int size){TextView v=new TextView(parent.getContext());v.setText(text);v.setTextSize(size);v.setTextColor(INK);v.setTypeface(null,Typeface.BOLD);v.setPadding(0,dp(v.getContext(),4),0,dp(v.getContext(),8));parent.addView(v);return v;}
 static LinearLayout card(LinearLayout parent,String title){Context c=parent.getContext();LinearLayout box=new LinearLayout(c);box.setOrientation(LinearLayout.VERTICAL);int p=dp(c,12);box.setPadding(p,p,p,p);box.setBackground(surface(c,0xffffffff,18));box.setElevation(dp(c,3));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(c,2),dp(c,6),dp(c,2),dp(c,8));parent.addView(box,lp);if(!title.isEmpty())label(box,title,15);return box;}
 static void input(EditText e){Context c=e.getContext();e.setTextColor(INK);e.setHintTextColor(MUTED);e.setTextSize(15);e.setBackground(surface(c,0xfff5f9fd,12));e.setPadding(dp(c,12),dp(c,10),dp(c,12),dp(c,10));e.setMinHeight(dp(c,48));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(c,4),0,dp(c,8));e.setLayoutParams(lp);}
 static void button(Button b,boolean primary){Context c=b.getContext();b.setAllCaps(false);b.setTextSize(13);b.setMinWidth(0);b.setMinimumWidth(0);b.setMinHeight(dp(c,48));b.setMinimumHeight(dp(c,48));b.setPadding(dp(c,6),dp(c,4),dp(c,6),dp(c,4));b.setMaxLines(2);b.setTextColor(new ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled},new int[]{}},new int[]{0xff8b9caa,primary?0xffffffff:INK}));b.setBackgroundTintList(null);b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x224499dd),surface(c,primary?BLUE:0xffedf5ff,12),null));b.setElevation(dp(c,primary?2:1));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-2,1);lp.setMargins(dp(c,3),dp(c,4),dp(c,3),dp(c,4));b.setLayoutParams(lp);}
}
