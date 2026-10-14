package com.junshi.assistant;
import org.junit.Test;
import static org.junit.Assert.*;
public class UrlPolicyTest {
 @Test public void acceptsHttps(){assertEquals("https://101.34.253.116",UrlPolicy.base("https://101.34.253.116/app"));}
 @Test public void refusesDowngrade(){assertFalse(UrlPolicy.sameOrigin("https://example.com","http://example.com/app"));}
 @Test public void refusesForeignOrigin(){assertFalse(UrlPolicy.sameOrigin("https://example.com","https://evil.example/app"));}
 @Test(expected=IllegalArgumentException.class) public void refusesCredentials(){UrlPolicy.base("https://user:password@example.com");}
}
