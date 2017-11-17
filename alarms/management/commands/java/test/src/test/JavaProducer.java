package test;

import java.util.UUID;
import java.util.concurrent.LinkedBlockingQueue;

public class JavaProducer {

	private LinkedBlockingQueue<Object> messages;
	
	public JavaProducer(){
		
		messages = new LinkedBlockingQueue<Object>(10);
		
		Thread produce = new Thread(){
			public void run(){
				while(true){
					try{
						String data = UUID.randomUUID().toString();
						messages.put(data);
						System.out.print(messages.size());
						Thread.sleep(250);
					}
					catch(InterruptedException e){e.printStackTrace();}
				}
			}
		};
		
		produce.setDaemon(true);
		produce.start();
		
	}
	
	public String getMessage() throws InterruptedException {
		return (String) this.messages.take();
	}
		
}
