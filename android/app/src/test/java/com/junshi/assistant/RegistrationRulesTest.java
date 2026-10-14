package com.junshi.assistant;
import org.junit.Test;
import static org.junit.Assert.*;

public class RegistrationRulesTest {
 @Test public void acceptsActualServerBoundaries(){
  assertNull(RegistrationRules.error("A._", "a".repeat(12)));
  assertNull(RegistrationRules.error("a".repeat(64), "密".repeat(256)));
  assertNull(RegistrationRules.error("user-01", "😀".repeat(12)));
 }
 @Test public void rejectsUnsupportedAccounts(){
  for(String name:new String[]{"ab","a".repeat(65),"用户名","abc def","abc@def","abc\n"})
   assertNotNull(RegistrationRules.error(name,"a".repeat(12)));
 }
 @Test public void countsUnicodeCharactersRatherThanUtf16Units(){
  assertNotNull(RegistrationRules.error("abc","😀".repeat(6)));
  assertNotNull(RegistrationRules.error("abc","a".repeat(257)));
 }
}
