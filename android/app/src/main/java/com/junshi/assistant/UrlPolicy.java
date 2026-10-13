package com.junshi.assistant;
import java.net.URI;

public final class UrlPolicy {
    private UrlPolicy() {}
    public static String base(String value) {
        try {
            URI u = new URI(value.trim());
            if (!"https".equalsIgnoreCase(u.getScheme()) || u.getHost()==null || u.getRawUserInfo()!=null || u.getRawQuery()!=null || u.getRawFragment()!=null
                || !(u.getPath().isEmpty() || u.getPath().equals("/") || u.getPath().equals("/app"))) throw new Exception();
            return new URI("https", null, u.getHost(), u.getPort(), null, null, null).toASCIIString();
        } catch (Exception e) { throw new IllegalArgumentException("请填写 HTTPS 服务器地址，例如 https://你的服务器IP；也可粘贴 /app 地址。"); }
    }
    public static boolean sameOrigin(String origin, String url) {
        try { URI a=URI.create(origin),b=URI.create(url);return "https".equals(b.getScheme()) && a.getHost().equalsIgnoreCase(b.getHost())
            && (a.getPort()==-1?443:a.getPort())==(b.getPort()==-1?443:b.getPort()) && b.getUserInfo()==null; }
        catch(Exception e){return false;}
    }
}
