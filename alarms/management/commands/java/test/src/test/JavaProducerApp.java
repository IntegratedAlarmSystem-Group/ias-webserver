package test;

import py4j.GatewayServer;

public class JavaProducerApp {

	private JavaProducer source = new JavaProducer();
	
	public String getMessage() throws InterruptedException{
		return this.source.getMessage();
	}
	
	public static void close() {
		System.exit(0);
	}

	public static void main(String[] args) {
		JavaProducerApp app = new JavaProducerApp();
		GatewayServer server = new GatewayServer(app);
		server.start();
	}

}