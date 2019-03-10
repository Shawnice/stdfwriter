import unittest
from .recheaders import *


class STDFWriterTest(unittest.TestCase):

    def setUp(self):
        self.inf = open("test.stdf", "wb")

    def test_write_stdf(self):
        far = FAR(CPU_TYPE=2, STDF_VER=4)
        far.write_record(self.inf)

        mir = MIR(SETUP_T=1546102685, START_T=1546102693, STAT_NUM=1, MODE_COD="P", BURN_TIM=65535, LOT_ID="ABCDEFG",
                  PART_TYP="XXXXXA", NODE_NAM="XXXXX34", TSTR_TYP="Test_Type", JOB_NAM="ABCDEFGHIJKLMNI.txt",
                  JOB_REV="", OPER_NAM="0000", EXEC_TYP="XX-YY", EXEC_VER="1.01.1", TEST_COD="RT", TST_TEMP="25C",
                  FACIL_ID="HEARTTEST", SPEC_NAM="CP", FLOOR_ID="CP")
        mir.write_record(self.inf)

        sdr = SDR(HEAD_NUM=0, SITE_GRP=255, SITE_CNT=16, SITE_NUM=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                  CARD_ID="AAAA-BB-CC-DD", LOAD_ID="6680")
        sdr.write_record(self.inf)

        for i in range(1, 6):
            for j in range(1, 16):
                pmr = PMR(PMR_INDX=i, CHAN_TYP=65535, CHAN_NAM="2.b2", PHY_NAM="Test", LOG_NAM="AC", HEAD_NUM=0, SITE_NUM=j)
                pmr.write_record(self.inf)

        pgr = PGR(GRP_INDX=32768, GRP_NAM="DC", INDX_CNT=16, PMR_INDX=[58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73])
        pgr.write_record(self.inf)
        pgr = PGR(GRP_INDX=32769, GRP_NAM="POSITIVE", INDX_CNT=2, PMR_INDX=[74,76])
        pgr.write_record(self.inf)
        pgr = PGR(GRP_INDX=32770, GRP_NAM="NEGITIVE", INDX_CNT=2, PMR_INDX=[75,77])
        pgr.write_record(self.inf)
        pgr = PGR(GRP_INDX=32771, GRP_NAM="POOL", INDX_CNT=2, PMR_INDX=[6,7])
        pgr.write_record(self.inf)

        plr = PLR(GRP_CNT=25,
                  GRP_INDX=[1, 2, 3, 4, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 54, 55, 56, 57, 32768, 32769, 32770, 32771, 32772, 32773, 32774],
                  GRP_MODE=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  GRP_RADX=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  PGM_CHAR=["*********", "*********", "*********", "*********", "*********", "*********", "*********", "*********", "*********",
                            "*********", "*********", "*********", "*********", "*********", "*********", "*********", "*********", "*********",
                            "*********", "*********", "*********", "*********", "*********", "*********", "*********"],
                  RTN_CHAR=["+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++",
                            "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++", "+++++"])
        plr.write_record(self.inf)

        wcr = WCR(WF_FLAT="U", CENTER_X=0, CENTER_Y=0, POS_X="R", POS_Y="D")
        wcr.write_record(self.inf)

        wir = WIR(HEAD_NUM=1, START_T=1546920469, WAFER_ID="20")
        wir.write_record(self.inf)

        for i in range(16):
            pir = PIR(HEAD_NUM=1, SITE_NUM=i)
            pir.write_record(self.inf)

        bps = BPS(SEQ_NAME="Flow")
        bps.write_record(self.inf)

        for i in range(10):
            for j in range(16):
                ptr = PTR(TEST_NUM=i, HEAD_NUM=1, SITE_NUM=j, TEST_FLG=0, PARM_FLG=0, RESULT=0.030896000564098358,
                          TEST_TXT="Test Item Name is ???", OPT_FLAG=0b11001110, UNITS="s", C_RESFMT="%5.2g",
                          C_LLMFMT="%5.2g", C_HLMFMT="%5.2g")
                ptr.write_record(self.inf)

        eps = EPS()
        eps.write_record(self.inf)

        for i in range(16):
            prr = PRR(HEAD_NUM=1, SITE_NUM=i, PART_FLG=0, NUM_TEST=6, HARD_BIN=1, SOFT_BIN=1,
                  X_COORD=53, Y_COORD=14, TEST_T=1546105693, PART_ID="1")
            prr.write_record(self.inf)

        for i in range(16):
            pir = PIR(HEAD_NUM=1, SITE_NUM=i)
            pir.write_record(self.inf)

        wrr = WRR(HEAD_NUM=1, FINISH_T=1546920536, PART_CNT=24957, RTST_CNT=0, ABRT_CNT=0,
                  GOOD_CNT=20613, WAFER_ID="20")
        wrr.write_record(self.inf)

        tsr = TSR(HEAD_NUM=255, SITE_NUM=255, TEST_TYP="P", TEST_NUM=2, EXEC_CNT=24957, FAIL_CNT=0,
                  ALRM_CNT=0, TEST_NAM="Laekage", SEQ_NAME="LEAK")
        tsr.write_record(self.inf)

        hbr = HBR(HEAD_NUM=255, SITE_NUM=0, HBIN_NUM=1, HBIN_CNT=20613)
        hbr.write_record(self.inf)

        pcr = PCR(HEAD_NUM=1, SITE_NUM=0, PART_CNT=1526, RTST_CNT=0, ABRT_CNT=0, GOOD_CNT=1272)
        pcr.write_record(self.inf)

        mrr = MRR(FINISH_T=1546105693)
        mrr.write_record(self.inf)

    def tearDown(self):
        self.inf.close()


if __name__ == '__main__':
    unittest.main()
