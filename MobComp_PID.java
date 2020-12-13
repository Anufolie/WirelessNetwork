package layer2_802Algorithms;

import plot.JEMultiPlotter;

import java.util.ArrayList;
import java.util.Arrays;

import kernel.JETime;
import layer1_802Phy.JE802PhyMode;
import layer2_80211Mac.JE802_11BackoffEntity;
import layer2_80211Mac.JE802_11Mac;
import layer2_80211Mac.JE802_11MacAlgorithm;

class PID {
	double kp , ki , kd ;
	double minOut = -1.0, maxOut = 1.0;

	double pErr, dErr, iErr;
	double prevInput, input, target, output;

	PID() {
	}

	PID(double target, double kp, double ki, double kd) {
		this.target = target;
		this.kp = kp;
		this.ki = ki;
		this.kd = kd;
		
	}

	double compute(double input) {
		this.input = input;
		pErr = target - input;
		dErr = (input - prevInput);
		iErr += pErr;

		// clamp integral part
		if (iErr > maxOut)
			iErr = maxOut;
		else if (iErr < minOut)
			iErr = minOut;

		// apply weights and sum parts
		output = kp * pErr + ki * iErr + kd * dErr;

		// save previous input
		prevInput = input;

		return output;
	}

	@Override
	public String toString() {
		return String.format("Output = kp*%7.4f + ki*%7.4f + kd*%7.4f = %7.4f", pErr, iErr, dErr, output);
	}
}

public class MobComp_PID extends JE802_11MacAlgorithm {

	private JE802_11BackoffEntity theBackoffEntityAC01;

	private double theSamplingTime_sec;

	// extra
	/*static String[] phyModes = { "BPSK12", "BPSK34", "QPSK12", "QPSK34", "16QAM12", "16QAM34", "64QAM23", "64QAM34" };
	int phyMode = 3;*/
	double target = 0.8 ;
	
	private PID pidQueue = new PID (1, 1, 0.1, 0.2);
	private PID pidColl = new PID (0, 1, 0.1, 0.2);
	private PID pidAck = new PID (target,1.5, 1.0, 0.55);
	
	private long prevTx, prevAck;

	public MobComp_PID(String name, JE802_11Mac mac) {
		super(name, mac);
		this.theBackoffEntityAC01 = this.mac.getBackoffEntity(1);
		this.mac.getPhy().setCurrentPhyMode("64QAM34");

		message("This is station " + this.dot11MACAddress.toString() + ". MobComp algorithm: '" + this.algorithmName
				+ "'.", 100);
	}
	
	int PrevCol = 0;

	@Override
	public void compute() {

		this.mac.getMlme().setTheIterationPeriod(1); // the sampling period in seconds, which is the time between
														// consecutive calls of this method "compute()"
		this.theSamplingTime_sec = this.mac.getMlme().getTheIterationPeriod().getTimeS(); // this sampling time can only
																							// be read after the MLME
																							// was constructed.

		// ASSIGNMENT 04 - observe outcome: (might need to be stored from iteration to
		// iteration)
		int aQueueSize = this.theBackoffEntityAC01.getQueueSize();
		int aCurrentQueueSize = this.theBackoffEntityAC01.getCurrentQueueSize();
		double aCurrentTxPower_dBm = this.mac.getPhy().getCurrentTransmitPower_dBm();
		JE802PhyMode aCurrentPhyMode = this.mac.getPhy().getCurrentPhyMode();
		
		int collisionCnt = this.theBackoffEntityAC01.getTheCollisionCnt();
		double QueueRatio = (double) (aQueueSize - aCurrentQueueSize) / 100;
		long newAck = theBackoffEntityAC01.getTheAckCnt();
		long newTx = theBackoffEntityAC01.getTheTxCnt();
		
		int CWmin = this.theBackoffEntityAC01.getDot11EDCACWmin();
		int CWmax = this.theBackoffEntityAC01.getDot11EDCACWmax();
		JETime AIFS = this.theBackoffEntityAC01.getAIFS();
		
		double ackTxRatio;
		if (newTx - prevTx <= 0) { // no packets have been sent
			ackTxRatio = target;
		} else {
			ackTxRatio = (double) (newAck - prevAck) / (newTx - prevTx);
		}

		prevAck = newAck;
		prevTx = newTx;
		

		if (!Double.isNaN(ackTxRatio)) {
			double output = pidAck.compute(ackTxRatio);

			if (output > 1) {
				CWmin = Math.min(32, CWmin * 2); // increase window exponentially
				CWmax = Math.min(2048, CWmax * 2);
			} 
			else if (output < 0) {
				CWmin = Math.max(1, CWmin - 2); // decrease window
				CWmax = Math.max(64, CWmax - 128);
			}
		}
		
		
		this.theBackoffEntityAC01.setDot11EDCACWmin(CWmin);
		this.theBackoffEntityAC01.setDot11EDCACWmax(CWmax);
		
		/*double collIncrease = collisionCnt - PrevCol;
		
		this.PrevCol = collisionCnt ;
		
		double Cout = pidColl.compute(collIncrease);
		
		double Qout = pidQueue.compute(QueueRatio);*/
		
		//if (collIncrease )
		
		
		
		
		

		

		//this.mac.getPhy().setCurrentPhyMode(phyModes[phyMode]);

		if (dot11MACAddress == 1) {
			System.out.format("Current ratio: %5f, %s, %s, %s\n", ackTxRatio, pidAck.toString(),
					CWmin, CWmax);
		}

		this.mac.getPhy().setCurrentTransmitPower_dBm(0); // it is also possible to change the transmission power
															// (please not higher than 0dBm)
	}

	@Override
	public void plot() {
		if (plotter == null) {
			plotter = new JEMultiPlotter("PID Controller, Station " + this.dot11MACAddress.toString(), "max",
					"time [s]", "MAC Queue", this.theUniqueEventScheduler.getEmulationEnd().getTimeMs() / 1000.0, true);
//			plotter.addSeries("current");
			plotter.addSeries("Phy Mode Mbps");
			plotter.display();
		}

		double t = (Double) theUniqueEventScheduler.now().getTimeMs() / 1000.0;
		plotter.plot(t, theBackoffEntityAC01.getQueueSize(), 0);
//		plotter.plot(t, theBackoffEntityAC01.getCurrentQueueSize(), 1);
		int rate = this.mac.getPhy().getCurrentPhyMode().getRateMbps();

		plotter.plot(t, rate, 1);
	}

}
