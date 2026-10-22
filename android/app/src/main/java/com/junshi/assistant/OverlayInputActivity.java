package com.junshi.assistant;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * 小窗「输入」的落点。
 *
 * <p>键盘只能可靠地落在 Activity 窗口上。之前把小窗（TYPE_APPLICATION_OVERLAY）临时改成可聚焦，
 * 系统会在小窗和下层应用之间来回切换焦点，屏幕就一闪一闪。这里用一层透明 Activity 承载输入框，
 * 小窗始终保持 FLAG_NOT_FOCUSABLE，闪烁随之消失。
 */
public class OverlayInputActivity extends Activity {
    EditText text;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setSoftInputMode(
                WindowManager.LayoutParams.SOFT_INPUT_STATE_VISIBLE
                        | WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        Session session = (Session) getApplication();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(20), dp(16), dp(16));
        root.setBackgroundColor(0xf7ffffff);

        TextView title = new TextView(this);
        title.setText("输入对方的新消息");
        title.setTextSize(16);
        title.setPadding(0, 0, 0, dp(8));
        root.addView(title);

        text = new EditText(this);
        text.setHint("粘贴或输入对方刚发来的内容");
        text.setGravity(Gravity.TOP | Gravity.START);
        text.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        text.setMinLines(3);
        text.setMaxLines(6);
        text.setText(session.input == null ? "" : session.input);
        Theme.input(text);
        root.addView(text, new LinearLayout.LayoutParams(-1, dp(140)));

        LinearLayout row = new LinearLayout(this);
        row.setPadding(0, dp(12), 0, 0);
        Button fill = new Button(this);
        fill.setText("只填入小窗");
        fill.setAllCaps(false);
        Theme.button(fill, false);
        fill.setOnClickListener(v -> apply(session, false));
        Button generate = new Button(this);
        generate.setText("填入并生成");
        generate.setAllCaps(false);
        Theme.button(generate, true);
        generate.setOnClickListener(v -> apply(session, true));
        Button close = new Button(this);
        close.setText("取消");
        close.setAllCaps(false);
        Theme.button(close, false);
        close.setOnClickListener(v -> finish());
        row.addView(fill);
        row.addView(generate);
        row.addView(close);
        root.addView(row);

        setContentView(root);
        text.postDelayed(this::focusAndType, 120);
    }

    void apply(Session session, boolean generate) {
        String value = text.getText() == null ? "" : text.getText().toString();
        session.editInput(value);
        session.changed();
        if (generate) session.generate();
        finish();
    }

    void focusAndType() {
        text.requestFocus();
        text.setSelection(text.getText().length());
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null) imm.showSoftInput(text, InputMethodManager.SHOW_IMPLICIT);
    }

    int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
