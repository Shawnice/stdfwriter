"""
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,　but WITHOUT ANY WARRANTY; without even the implied warranty of　
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the　GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


from dtcodes import write_record_map, pack_len_map


class Record:
    """Basic class for processing STDF record data

    Attributes:
        rec_len: The number of bytes of data following the record header. REC_LEN does not
                 include the four bytes of the record header.
        rec_typ: An integer identifying a group of related STDF record types.
        rec_sub: An integer identifying a specific STDF record type within each REC_TYP group.
                 On REC_TYP and REC_SUB, see the next section.
        field_names(tuple(tuple)): each element contains field name and its data type
        field_values(dict): save the value of each field name

    Methods:
        cal_rec_len: calculate record's total length (not includes header length)
        write_record: write record data in to file
    """
    rec_len = 0
    rec_typ = 0
    rec_sub = 0
    field_names = None
    field_values = None

    def cal_rec_len(self):
        for f in self.field_names:
            if f[1] in pack_len_map:
                self.rec_len += pack_len_map[f[1]]
            elif f[1] == 'Cn':
                self.rec_len += len(self.field_values[f[0]]) + 1  # include first byte
            elif f[1] == 'Bn':
                self.rec_len += len(self.field_values[f[0]]) + 1
            elif f[1] == 'Dn':
                self.rec_len += len(self.field_values[f[0]]) + 2  # include first two bytes

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            write_record_map[f[1]](inf, self.field_values[f[0]])


class FAR(Record):
    """
    Function: Contains the information necessary to determine how to decode the STDF data
              contained in the file.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (0)
    REC_SUB         U*1             Record sub-type (10)

    CPU_TYPE        U*1             CPU type that wrote this file
    STDF_VER        U*1             STDF version number
    =================================================================================================
    Notes on Specific Fields:
    CPU_TYPE        Indicates which type of CPU wrote this STDF file. This information is useful for
                    determining the CPU-dependent data representation of the integer and floating point
                    fields in the file’s records. The valid values are:
                            0 = DEC PDP-11 and VAX processors. F and D floating point formats
                                will be used. G and H floating point formats will not be used.
                            1 = Sun 1, 2, 3, and 4 computers.
                            2 = Sun 386i computers, and IBM PC, IBM PC-AT, and IBM PC-XT
                                computers.
                        3-127 = Reserved for future use by Teradyne.
                      128-255 = Reserved for use by customers.
                    Acode defined heremay also be valid for otherCPUtypeswhose data formats are fully
                    compatible with that of the type listed here. Before using one of these codes for a CPU
                    type not listed here, please check with the Teradyne hotline, which can provide
                    additional information on CPU compatibility.

    STDF_VER        Identifies the version number of the STDF specification used in generating the data.
                    This allows data analysis programs to handle STDF specification enhancements.

    Location: Required as the first record of the file.
    """
    rec_typ = 0
    rec_sub = 10
    field_names = (
        ('CPU_TYPE', 'U1'),
        ('STDF_VER', 'U1')
    )

    def __init__(self, CPU_TYPE, STDF_VER):
        self.field_values = locals()


class ATR(Record):
    """
    Function: Used to record any operation that alters the contents of the STDF file. The name of the
              program and all its parameters should be recorded in the ASCII field provided in this
              record. Typically, this record will be used to track filter programs that have been
              applied to the data.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (0)
    REC_SUB         U*1             Record sub-type (20)

    MOD_TIM         U*4             Date and time of STDF file modification
    CMD_LINE        C*n             Command line of program
    =================================================================================================
    Frequency:      Optional. One for each filter or other data transformation program applied to the STDF
                    data.
    Location:       Between the File Attributes Record (FAR) and the Master Information Record (MIR).
                    The filter program that writes the altered STDF file must write its ATR immediately
                    after the FAR (and hence before any other ATRs that may be in the file). In this way,
                    multiple ATRs will be in reverse chronological order.

    Possible Use:   Determining whether a particular filter has been applied to the data.
    """
    rec_typ = 0
    rec_sub = 20
    field_names = (
        ('MOD_TIM', 'U4'),
        ('CMD_LINE', 'Cn')
    )

    def __init__(self, MOD_TIM, CMD_LINE):
        self.field_values = locals()


class MIR(Record):
    """
    Function: The MIR and the MRR (Master Results Record) contain all the global information that
            is to be stored for a tested lot of parts. Each data stream must have exactly one MIR,
            immediately after the FAR (and the ATRs, if they are used). This will allow any data
            reporting or analysis programs access to this information in the shortest possible
            amount of time.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (10)

    SETUP_T         U*4             Date and time of job setup
    START_T         U*4             Date and time first part tested
    STAT_NUM        U*1             Tester station number
    MODE_COD        C*1             Test mode code (e.g. prod, dev) space
    RTST_COD        C*1             Lot retest code space
    PROT_COD        C*1             Data protection code space
    BURN_TIM        U*2             Burn-in time (in minutes) 65,535
    CMOD_COD        C*1             Command mode code space
    LOT_ID          C*n             Lot ID (customer specified)
    PART_TYP        C*n             Part Type (or product ID)
    NODE_NAM        C*n             Name of node that generated data
    TSTR_TYP        C*n             Tester type
    JOB_NAM         C*n             Job name (test program name)
    JOB_REV         C*n             Job (test program) revision number length byte = 0
    SBLOT_ID        C*n             Sublot ID length byte = 0
    OPER_NAM        C*n             Operator name or ID (at setup time) length byte = 0
    EXEC_TYP        C*n             Tester executive software type length byte = 0
    EXEC_VER        C*n             Tester exec software version number length byte = 0
    TEST_COD        C*n             Test phase or step code length byte = 0
    TST_TEMP        C*n             Test temperature length byte = 0
    USER_TXT        C*n             Generic user text length byte = 0
    AUX_FILE        C*n             Name of auxiliary data file length byte = 0
    PKG_TYP         C*n             Package type length byte = 0
    FAMLY_ID        C*n             Product family ID length byte = 0
    DATE_COD        C*n             Date code length byte = 0
    FACIL_ID        C*n             Test facility ID length byte = 0
    FLOOR_ID        C*n             Test floor ID length byte = 0
    PROC_ID         C*n             Fabrication process ID length byte = 0
    OPER_FRQ        C*n             Operation frequency or step length byte = 0
    SPEC_NAM        C*n             Test specification name length byte = 0
    SPEC_VER        C*n             Test specification version number length byte = 0
    FLOW_ID         C*n             Test flow ID length byte = 0
    SETUP_ID        C*n             Test setup ID length byte = 0
    DSGN_REV        C*n             Device design revision length byte = 0
    ENG_ID          C*n             Engineering lot ID length byte = 0
    ROM_COD         C*n             ROM code ID length byte = 0
    SERL_NUM        C*n             Tester serial number length byte = 0
    SUPR_NAM        C*n             Supervisor name or ID length byte = 0
    =================================================================================================
    Frequency:      Always required. One per data stream.
    Location:       Immediately after the File Attributes Record (FAR) and the Audit Trail Records (ATR),
                    if ATRs are used.

    Possible Use:   Header information for all reports
    """
    rec_typ = 1
    rec_sub = 10
    field_names = (
        ('SETUP_T', 'U4'),
        ('START_T', 'U4'),
        ('STAT_NUM', 'U1'),
        ('MODE_COD', 'C1'),
        ('RTST_COD', 'C1'),
        ('PROT_COD', 'C1'),
        ('BURN_TIM', 'U2'),
        ('CMOD_COD', 'C1'),
        ('LOT_ID', 'Cn'),
        ('PART_TYP', 'Cn'),
        ('NODE_NAM', 'Cn'),
        ('TSTR_TYP', 'Cn'),
        ('JOB_NAM', 'Cn'),
        ('JOB_REV', 'Cn'),
        ('SBLOT_ID', 'Cn'),
        ('OPER_NAM', 'Cn'),
        ('EXEC_TYP', 'Cn'),
        ('EXEC_VER', 'Cn'),
        ('TEST_COD', 'Cn'),
        ('TST_TEMP', 'Cn'),
        ('USER_TXT', 'Cn'),
        ('AUX_FILE', 'Cn'),
        ('PKG_TYP', 'Cn'),
        ('FAMLY_ID', 'Cn'),
        ('DATE_COD', 'Cn'),
        ('FACIL_ID', 'Cn'),
        ('FLOOR_ID', 'Cn'),
        ('PROC_ID', 'Cn'),
        ('OPER_FRQ', 'Cn'),
        ('SPEC_NAM', 'Cn'),
        ('SPEC_VER', 'Cn'),
        ('FLOW_ID', 'Cn'),
        ('SETUP_ID', 'Cn'),
        ('DSGN_REV', 'Cn'),
        ('ENG_ID', 'Cn'),
        ('ROM_COD', 'Cn'),
        ('SERL_NUM', 'Cn'),
        ('SUPR_NAM', 'Cn')
    )

    def __init__(self, SETUP_T, START_T, STAT_NUM, LOT_ID, PART_TYP, NODE_NAM, TSTR_TYP, JOB_NAM,
                 MODE_COD=" ", RTST_COD=" ", PROT_COD=" ", BURN_TIM=65535, CMOD_COD=" ", JOB_REV="",
                 SBLOT_ID="", OPER_NAM="", EXEC_TYP="", EXEC_VER="", TEST_COD="", TST_TEMP="",
                 USER_TXT="", AUX_FILE="", PKG_TYP="", FAMLY_ID="", DATE_COD="", FACIL_ID="", FLOOR_ID="",
                 PROC_ID="", OPER_FRQ="", SPEC_NAM="", SPEC_VER="", FLOW_ID="", SETUP_ID="", DSGN_REV="",
                 ENG_ID="", ROM_COD="", SERL_NUM="", SUPR_NAM=""):
        self.field_values = locals()


class MRR(Record):
    """
    Function: The Master Results Record (MRR) is a logical extension of the Master Information
                Record (MIR). The data can be thought of as belonging with the MIR, but it is not
                available when the tester writes the MIR information. Each data stream must have
                exactly one MRR as the last record in the data stream.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (20)

    FINISH_T        U*4             Date and time last part tested
    DISP_COD        C*1             Lot disposition code space
    USR_DESC        C*n             Lot description supplied by user length byte = 0
    EXC_DESC        C*n             Lot description supplied by exec length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    DISP_COD        Supplied by the user to indicate the disposition of the lot of parts (or of the tester itself,
                    in the case of checker or AEL data). The meaning of DISP_COD values are user-defined.
                    A valid value is an ASCII alphanumeric character (0 - 9 or A - Z). A space indicates a
                    missing value.
    Frequency:      Exactly one MRR required per data stream.
    Location:       Must be the last record in the data stream.

    Possible Use:   Final Summary Sheet     Merged Summary Sheet
                    Datalog                 Test Results Synopsis Report
                    Wafer Map               Trend Plot
                    Histogram               ADART
                    Correlation             RTBM
                    Shmoo Plot              User Data
                    Repair Report
    """
    rec_typ = 1
    rec_sub = 20
    field_names = (
        ('FINISH_T', 'U4'),
        ('DISP_COD', 'C1'),
        ('USR_DESC', 'Cn'),
        ('EXC_DESC', 'Cn')
    )

    def __init__(self, FINISH_T, DISP_COD=" ", USR_DESC="", EXC_DESC=""):
        self.field_values = locals()


class PCR(Record):
    """
    Function: Contains the part count totals for one or all test sites. Each data stream must have at
                least one PCR to show the part count.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (30)

    HEAD_NUM        U*1             Test head number See note
    SITE_NUM        U*1             Test site number
    PART_CNT        U*4             Number of parts tested
    RTST_CNT        U*4             Number of parts retested 4,294,967,295
    ABRT_CNT        U*4             Number of aborts during testing 4,294,967,295
    GOOD_CNT        U*4             Number of good (passed) parts tested 4,294,967,295
    FUNC_CNT        U*4             Number of functional parts tested 4,294,967,295
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM        If this PCR contains a summary of the part counts for all test sites, this field must be
                    set to 255.
    GOOD_CNT,
    FUNC_CNT        A part is considered good when it is binned into one of the “passing” hardware bins. A
                    part is considered functional when it is good enough to test, whether it passes or not.
                    Parts that are incomplete or have shorts or opens are considered non-functional.
    Frequency:      There must be at least one PCR in the file: either one summary PCR for all test sites
                    (HEAD_NUM = 255), or one PCR for each head/site combination, or both.
    Location:       Anywhere in the data stream after the initial sequence (see page 14) and before the
                    MRR.When data is being recorded in real time, this record will usually appear near the
                    end of the data stream.

    Possible Use:   Final Summary Sheet         Merged Summary Sheet
                    Site Summary Sheet          Report for Lot Tracking System
    """
    rec_typ = 1
    rec_sub = 30
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('PART_CNT', 'U4'),
        ('RTST_CNT', 'U4'),
        ('ABRT_CNT', 'U4'),
        ('GOOD_CNT', 'U4'),
        ('FUNC_CNT', 'U4')
    )

    def __init__(self, HEAD_NUM, SITE_NUM, PART_CNT, RTST_CNT=4294967295, ABRT_CNT=4294967295, GOOD_CNT=4294967295, FUNC_CNT=4294967295):
        self.field_values = locals()


class HBR(Record):
    """
    Function: Stores a count of the parts “physically” placed in a particular bin after testing. (In
                wafer testing, “physical” binning is not an actual transfer of the chip, but rather is
                represented by a drop of ink or an entry in a wafer map file.) This bin count can be for
                a single test site (when parallel testing) or a total for all test sites. The STDF
                specification also supports a Software Bin Record (SBR) for logical binning categories.
                A part is “physically” placed in a hardware bin after testing. A part can be “logically”
                associated with a software bin during or after testing.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (40)

    HEAD_NUM        U*1             Test head number See note
    SITE_NUM        U*1             Test site number
    HBIN_NUM        U*2             Hardware bin number
    HBIN_CNT        U*4             Number of parts in bin
    HBIN_PF         C*1             Pass/fail indication space
    HBIN_NAM        C*n             Name of hardware bin length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM        If this HBR contains a summary of the hardware bin counts for all test sites, this field
                    must be set to 255.
    HBIN_NUM        Has legal values in the range 0 to 32767.
    HBIN_PF         This field indicates whether the hardware bin was a passing or failing bin. Valid values
                    for this field are:
                            P = Passingbin
                            F = Failing bin
                        space = Unknown
    Frequency:      One per hardware bin for each site. One per hardware bin for bin totals.
                    May be included to name unused bins.
    Location:       Anywhere in the data stream after the initial sequence (see page 14) and before the
                    MRR. When data is being recorded in real time, this record usually appears near the
                    end of the data stream.

    Possible Use:   Final Summary Sheet         Merged Summary Sheet
                    Site Summary Sheet          Report for Lot Tracking System
    """
    rec_typ = 1
    rec_sub = 40
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('HBIN_NUM', 'U2'),
        ('HBIN_CNT', 'U4'),
        ('HBIN_PF', 'C1'),
        ('HBIN_NAM', 'Cn')
    )

    def __init__(self, HEAD_NUM, SITE_NUM, HBIN_NUM, HBIN_CNT, HBIN_PF=" ", HBIN_NAM=""):
        self.field_values = locals()


class SBR(Record):
    """
    Function: Stores a count of the parts associated with a particular logical bin after testing. This
                bin count can be for a single test site (when parallel testing) or a total for all test sites.
                The STDF specification also supports a Hardware Bin Record (HBR) for actual physical
                binning. A part is “physically” placed in a hardware bin after testing. A part can be
                “logically” associated with a software bin during or after testing.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (40)

    HEAD_NUM        U*1             Test head number See note
    SITE_NUM        U*1             Test site number
    SBIN_NUM        U*2             Hardware bin number
    SBIN_CNT        U*4             Number of parts in bin
    SBIN_PF         C*1             Pass/fail indication space
    SBIN_NAM        C*n             Name of hardware bin length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM        If this HBR contains a summary of the hardware bin counts for all test sites, this field
                    must be set to 255.
    HBIN_NUM        Has legal values in the range 0 to 32767.
    HBIN_PF         This field indicates whether the hardware bin was a passing or failing bin. Valid values
                    for this field are:
                            P = Passingbin
                            F = Failing bin
                        space = Unknown
    Frequency:      One per hardware bin for each site. One per hardware bin for bin totals.
                    May be included to name unused bins.
    Location:       Anywhere in the data stream after the initial sequence (see page 14) and before the
                    MRR. When data is being recorded in real time, this record usually appears near the
                    end of the data stream.

    Possible Use:   Final Summary Sheet         Merged Summary Sheet
                    Site Summary Sheet          Report for Lot Tracking System
    """
    rec_typ = 1
    rec_sub = 50
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('SBIN_NUM', 'U2'),
        ('SBIN_CNT', 'U4'),
        ('SBIN_PF', 'C1'),
        ('SBIN_NAM', 'Cn')
    )

    def __init__(self, HEAD_NUM, SITE_NUM, SBIN_NUM, SBIN_CNT, SBIN_PF=" ", SBIN_NAM=""):
        self.field_values = locals()


class PMR(Record):
    """
    Function: Provides indexing of tester channel names, and maps them to physical and logical pin
                names. Each PMR defines the information for a single channel/pin combination. See
                “Using the Pin Mapping Records” on page 77.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (60)

    PMR_INDX        U*2             Unique index associated with pin
    CHAN_TYP        U*2             Channel type 0
    CHAN_NAM        C*n             Channel name length byte = 0
    PHY_NAM         C*n             Physical name of pin length byte = 0
    LOG_NAM         C*n             Logical name of pin length byte = 0
    HEAD_NUM        U*1             Head number associated with channel 1
    SITE_NUM        U*1             Site number associated with channel 1
    =================================================================================================
    Notes on Specific Fields:
    PMR_INDX        This number is used to associate the channel and pin name information with data in
                    the FTR or MPR. Reporting programs can then look up the PMR index and choose which
                    of the three associated names they will use.
                    The range of legal PMR indexes is 1 - 32,767.
                    The size of the FAIL_PIN and SPIN_MAP arrays in the FTR are directly proportional to
                    the highest PMR index number. Therefore, it is important to start PMR indexes with a
                    low number and use consecutive numbers if possible.
    CHAN_TYP        The channel type values are tester-specific. Please refer to the tester documentation for
                    a list of the valid tester channel types and codes.
    HEAD_NUM,
    SITE_NUM        If a test system does not support parallel testing and does not have a standard way of
                    identifying its single test site or head, these fields should be set to 1. If missing, the
                    value of these fields will default to 1.
    Frequency:      One per channel/pin combination used in the test program.
                    Reuse of a PMR index number is not permitted.
    Location:       After the initial sequence (see page 14) and before the first PGR, PLR, FTR, or MPR that
                    uses this record’s PMR_INDX value.

    Possible Use:   Functional Datalog      Functional Histogram
    """
    rec_typ = 1
    rec_sub = 60
    field_names = (
        ('PMR_INDX', 'U2'),
        ('CHAN_TYP', 'U2'),
        ('CHAN_NAM', 'Cn'),
        ('PHY_NAM', 'Cn'),
        ('LOG_NAM', 'Cn'),
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1')
    )

    def __init__(self, PMR_INDX, CHAN_TYP=0, CHAN_NAM="", PHY_NAM="", LOG_NAM="", HEAD_NUM=1, SITE_NUM=1):
        self.field_values = locals()


class PGR(Record):
    """
    Function: Associates a name with a group of pins. See “Using the Pin Mapping Records” on page 77.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (62)

    GRP_INDX        U*2             Unique index associated with pin group
    GRP_NAM         C*n             Name of pin group                       length byte = 0
    INDX_CNT        U*2             Count (k) of PMR indexes
    PMR_INDX        kxU*2           Array of indexes for pins in the group  INDX_CNT = 0
    =================================================================================================
    Notes on Specific Fields:
    GRP_INDX        The range of legal group index numbers is 32,768 - 65,535.
    INDX_CNT,
    PMR_INDX        PMR_INDX is an array of PMR indexes whose length is defined by INDX_CNT. The order
                    of the PMR indexes should be from most significant to least significant bit in the pin
                    group (regardless of the order of PMR index numbers).
    Frequency:      One per pin group defined in the test program.
    Location:       After all the PMRs whose PMR index values are listed in the PMR_INDX array of this
                    record; and before the first PLR that uses this record’s GRP_INDX value.

    Possible Use:   Functional Datalog
    """
    rec_typ = 1
    rec_sub = 62
    field_names = (
        ('GRP_INDX', 'U2'),
        ('GRP_NAM', 'Cn'),
        ('INDX_CNT', 'U2'),
        ('PMR_INDX', 'kxU2')
    )

    def __init__(self, GRP_INDX, INDX_CNT, GRP_NAM="", PMR_INDX=0):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add PMR_INDX length
        self.rec_len += pack_len_map["U2"] * self.field_values["INDX_CNT"]

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU2":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["INDX_CNT"])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class PLR(Record):
    """
    Function: Defines the current display radix and operating mode for a pin or pin group. See “Using
                the Pin Mapping Records” on page 77.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (63)

    GRP_CNT         U*2             Count (k) of pins or pin groups
    GRP_INDX        kxU*2           Array of pin or pin group indexes
    GRP_MODE        kxU*2           Operating mode of pin group             0
    GRP_RADX        kxU*1           Display radix of pin group              0
    PGM_CHAR        kxC*n           Program state encoding characters       length byte = 0
    RTN_CHAR        kxC*n           Return state encoding characters        length byte = 0
    PGM_CHAL        kxC*n           Program state encoding characters       length byte = 0
    RTN_CHAL        kxC*n           Return state encoding characters        length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    GRP_CNT         GRP_CNT defines the number of pins or pin groups whose radix and mode are being
                    defined. Therefore, it defines the size of each of the arrays that follow in the record.
                    GRP_CNT must be greater than zero.
    GRP_MODE        The following are valid values for the pin group mode:
                        00 = Unknown
                        10 = Normal
                        20 = SCIO (Same Cycle I/O)
                        21 = SCIO Midband
                        22 = SCIO Valid
                        23 = SCIOWindow Sustain
                        30 = Dual drive (two drive bits per cycle)
                        31 = Dual drive Midband
                        32 = Dual drive Valid
                        33 = Dual drive Window Sustain
                    Unused pin group modes in the range of 1 through 32,767 are reserved for future use.
                    Pin group modes 32,768 through 65,535 are available for customer use.
    GRP_RADX        The following are valid values for the pin group display radix:
                        0 = Use display program default
                        2 = Display in Binary
                        8 = DisplayinOctal
                        10 = Display in Decimal
                        16 = Display in Hexadecimal
                        20 = Display as symbolic
    PGM_CHAR,
    PGM_CHAL        These ASCII characters are used to display the programmed state in the FTR or MPR.
                    Use of these character arrays makes it possible to store tester-dependent display
                    representations in a tester-independent format. If a single character is used to
                    represent each programmed state, then only the PGM_CHAR array need be used. If two
                    characters represent each state, then the first (left) character is stored in PGM_CHAL
                    and the second (right) character is stored in PGM_CHAR.
    RTN_CHAR,
    RTN_CHAL        These ASCII characters are used to display the returned state in the FTR or MPR. Use
                    of these character arrays makes it possible to store tester-dependent display
                    representations in a tester-independent format. If a single character is used to
                    represent each returned state, then only the RTN_CHAR array need be used. If two
                    characters represent each state, then the first (left) character is stored in RTN_CHAL
                    and the second (right) character is stored in RTN_CHAR.
    Note on Missing/Invalid Data Flags:
        For each field, the missing/invalid data flag applies to each member of the
        array, not to the array as a whole. Empty arrays (or empty members of
        arrays) can be omitted if they occur at the end of the record. Otherwise,
        each array must have the number of members indicated by GRP_CNT. You
        can then use the field’s missing/invalid data flag to indicate which array
        members have no data. For example, if GRP_CNT = 3, and if PGM_CHAL
        contains no data (but RTN_CHAL, which appears after PGM_CHAL, does),
        then PGM_CHAL should be an array of three missing/invalid data flags: 0,
        0, 0.
    Frequency:      One or more whenever the usage of a pin or pin group changes in the test program.
    Location:       After all the PMRs and PGRs whose PMR index values and pin group index values are
                    listed in the GRP_INDX array of this record; and before the first FTR that references pins
                    or pin groups whose modes are defined in this record.

    Possible Use:   Functional Datalog
    """
    rec_typ = 1
    rec_sub = 63
    field_names = (
        ('GRP_CNT', 'U2'),
        ('GRP_INDX', 'kxU2'),
        ('GRP_MODE', 'kxU2'),
        ('GRP_RADX', 'kxU1'),
        ('PGM_CHAR', 'kxCn'),
        ('RTN_CHAR', 'kxCn'),
        ('PGM_CHAL', 'kxCn'),
        ('RTN_CHAL', 'kxCn')
    )

    def __init__(self, GRP_CNT, GRP_INDX, GRP_MODE=0, GRP_RADX=0, PGM_CHAR="", RTN_CHAR="",
                 PGM_CHAL="", RTN_CHAL=""):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add GRP_INDX length
        self.rec_len += pack_len_map["U2"] * len(self.field_values["GRP_INDX"])
        # add GRP_MODE length
        self.rec_len += pack_len_map["U2"] * len(self.field_values["GRP_MODE"])
        # add GRP_RADX length
        self.rec_len += pack_len_map["U1"] * len(self.field_values["GRP_RADX"])
        # add PGM_CHAR length
        self.rec_len += sum([len(x) + 1 for x in self.field_values["PGM_CHAR"]])
        # add RTN_CHAR length
        self.rec_len += sum([len(x) + 1 for x in self.field_values["RTN_CHAR"]])
        # add PGM_CHAL length
        self.rec_len += sum([len(x) + 1 for x in self.field_values["PGM_CHAL"]])
        # add RTN_CHAL length
        self.rec_len += sum([len(x) + 1 for x in self.field_values["RTN_CHAL"]])

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU2" or f[1] == "kxU1" or f[1] == "kxCn":
                write_record_map[f[1]](inf, self.field_values[f[0]], len(self.field_values[f[0]]))
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class RDR(Record):
    """
    Function: Signals that the data in this STDF file is for retested parts. The data in this record,
                combined with information in the MIR, tells data filtering programs what data to
                replace when processing retest data.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (1)
    REC_SUB         U*1             Record sub-type (70)

    NUM_BINS        U*2             Number (k) of bins being retested
    RTST_BIN        kxU*2           Array of retest bin numbers             NUM_BINS = 0
    =================================================================================================
    Notes on Specific Fields:
    NUM_BINS,
    RTST_BIN        NUM_BINS indicates the number of hardware bins being retested and therefore the size
                    of the RTST_BIN array that follows. If NUM_BINS is zero, then all bins in the lot are being
                    retested and RTST_BIN is omitted.
                    The LOT_ID, SUBLOT_ID, and TEST_COD of the current STDF file should match those of
                    the STDF file that is being retested, so the data can be properly merged at a later time.

    Frequency:      Optional. One per data stream.
    Location:       If this record is used, it must appear immediately after theMaster Information Record
                    (MIR).

    Possible Use:   Tells data filtering programs how to handle retest data.
    """
    rec_typ = 1
    rec_sub = 70
    field_names = (
        ('NUM_BINS', 'U2'),
        ('RTST_BIN', 'kxU2')
    )

    def __init__(self, NUM_BINS, RTST_BIN=0):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add RTST_BIN length
        self.rec_len += pack_len_map["U2"] * self.field_values["NUM_BINS"]

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU2":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["NUM_BINS"])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class SDR(Record):
    """
     Function: Contains the configuration information for one or more test sites, connected to one test
               head, that compose a site group.

     Data Fields:
     Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
     =================================================================================================
     REC_LEN         U*2             Bytes of data following header
     REC_TYP         U*1             Record type (1)
     REC_SUB         U*1             Record sub-type (80)

     HEAD_NUM        U*1             Test head number
     SITE_GRP        U*1             Site group number
     SITE_CNT        U*1             Number (k) of test sites in site group
     SITE_NUM        kxU*1           Array of test site numbers
     HAND_TYP        C*n             Handler or prober type length byte = 0
     HAND_ID         C*n             Handler or prober ID length byte = 0
     CARD_TYP        C*n             Probe card type length byte = 0
     CARD_ID         C*n             Probe card ID length byte = 0
     LOAD_TYP        C*n             Load board type length byte = 0
     LOAD_ID         C*n             Load board ID length byte = 0
     DIB_TYP         C*n             DIB board type length byte = 0
     DIB_ID          C*n             DIB board ID length byte = 0
     CABL_TYP        C*n             Interface cable type length byte = 0
     CABL_ID         C*n             Interface cable ID length byte = 0
     CONT_TYP        C*n             Handler contactor type length byte = 0
     CONT_ID         C*n             Handler contactor ID length byte = 0
     LASR_TYP        C*n             Laser type length byte = 0
     LASR_ID         C*n             Laser ID length byte = 0
     EXTR_TYP        C*n             Extra equipment type field length byte = 0
     EXTR_ID         C*n             Extra equipment ID length byte = 0
     =================================================================================================
     Notes on Specific Fields:
     SITE_GRP        Specifies a site group number (called a station number on some testers) for the group
                     of sites whose configuration is defined by this record. Note that this is different from
                     the station number specified in the MIR, which refers to a software station only.
                     The value in this field must be unique within the STDF file.
     SITE_CNT,
     SITE_NUM        SITE_CNT tells how many sites are in the site group that the current SDR configuration
                     applies to. SITE_NUM is an array of those site numbers.
     _TYP fields     These are the type or model number of the interface or peripheral equipment being
                     used for testing:
                         HAND_TYP,CARD_TYP,LOAD_TYP,DIB_TYP,
                         CABL_TYP,CONT_TYP,LASR_TYP,EXTR_TYP
     _ID fields      These are the IDs or serial numbers of the interface or peripheral equipment being
                     used for testing:
                         HAND_ID,CARD_ID,LOAD_ID,DIB_ID,
                         CABL_ID,CONT_ID,LASR_ID,EXTR_ID
     Frequency:      One for each site or group of sites that is differently configured.
     Location:       Immediately after the MIR and RDR (if an RDR is used).

     Possible Use:   Correlation of yield to interface or peripheral equipment
    """
    rec_typ = 1
    rec_sub = 80
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_GRP', 'U1'),
        ('SITE_CNT', 'U1'),
        ('SITE_NUM', 'kxU1'),
        ('HAND_TYP', 'Cn'),
        ('HAND_ID', 'Cn'),
        ('CARD_TYP', 'Cn'),
        ('CARD_ID', 'Cn'),
        ('LOAD_TYP', 'Cn'),
        ('LOAD_ID', 'Cn'),
        ('DIB_TYP', 'Cn'),
        ('DIB_ID', 'Cn'),
        ('CABL_TYP', 'Cn'),
        ('CABL_ID', 'Cn'),
        ('CONT_TYP', 'Cn'),
        ('CONT_ID', 'Cn'),
        ('LASR_TYP', 'Cn'),
        ('LASR_ID', 'Cn'),
        ('EXTR_TYP', 'Cn'),
        ('EXTR_ID', 'Cn')
    )

    def __init__(self, HEAD_NUM, SITE_GRP, SITE_CNT, SITE_NUM, HAND_TYP="", HAND_ID="",
                 CARD_TYP="", CARD_ID="", LOAD_TYP="", LOAD_ID="", DIB_TYP="", DIB_ID="", CABL_TYP="",
                 CABL_ID="", CONT_TYP="", CONT_ID="", LASR_TYP="", LASR_ID="", EXTR_TYP="", EXTR_ID=""):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add SITE_NUM length
        self.rec_len += pack_len_map["U1"] * self.field_values["SITE_CNT"]

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU1":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["SITE_CNT"])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class WIR(Record):
    """
    Function: Acts mainly as a marker to indicate where testing of a particular wafer begins for each
            wafer tested by the job plan. The WIR and the Wafer Results Record (WRR) bracket all
            the stored information pertaining to one tested wafer. This record is used only when
            testing at wafer probe. A WIR/WRR pair will have the same HEAD_NUM and SITE_GRP
            values

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (2)
    REC_SUB         U*1             Record sub-type (10)

    HEAD_NUM        U*1             Test head number
    SITE_GRP        U*1             Site group number                       255
    START_T         U*4             Date and time first part tested
    WAFER_ID        C*n             Wafer ID                                length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    SITE_GRP        Refers to the site group in the SDR. This is ameans of relating the wafer information
                    to the configuration of the equipment used to test it. If this information is not known,
                    or the tester does not support the concept of site groups, this field should be set to 255.
    WAFER_ID        Is optional, but is strongly recommended in order to make the resultant data files as
                    useful as possible.
    Frequency:      One per wafer tested.
    Location:       Anywhere in the data stream after the initial sequence (see page 14) and before the
                    MRR.Sent before testing each wafer.

    Possible Use:   Wafer Summary Sheet         Datalog
                    Wafer Map
    """
    rec_typ = 2
    rec_sub = 10
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_GRP', 'U1'),
        ('START_T', 'U4'),
        ('WAFER_ID', 'Cn')
    )

    def __init__(self, HEAD_NUM, START_T, SITE_GRP=255, WAFER_ID=""):
        self.field_values = locals()


class WRR(Record):
    """
    Function: Contains the result information relating to each wafer tested by the job plan. The WRR
                and the Wafer Information Record (WIR) bracket all the stored information pertaining
                to one tested wafer. This record is used only when testing at wafer probe time. A
                WIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (2)
    REC_SUB         U*1             Record sub-type (20)

    HEAD_NUM        U*1             Test head number
    SITE_GRP        U*1             Site group number                       255
    FINISH_T        U*4             Date and time last part tested
    PART_CNT        U*4             Number of parts tested
    RTST_CNT        U*4             Number of parts retested                4,294,967,295
    ABRT_CNT        U*4             Number of aborts during testing         4,294,967,295
    GOOD_CNT        U*4             Number of good (passed) parts tested    4,294,967,295
    FUNC_CNT        U*4             Number of functional parts tested       4,294,967,295
    WAFER_ID        C*n             Wafer ID length byte = 0
    FABWF_ID        C*n             Fab wafer ID                            length byte = 0
    FRAME_ID        C*n             Wafer frame ID                          length byte = 0
    MASK_ID         C*n             Wafer mask ID                           length byte = 0
    USR_DESC        C*n             Wafer description supplied by user      length byte = 0
    EXC_DESC        C*n             Wafer description supplied by exec      length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    SITE_GRP        Refers to the site group in the SDR. This is ameans of relating the wafer information
                    to the configuration of the equipment used to test it. If this information is not known,
                    or the tester does not support the concept of site groups, this field should be set to 255.
    WAFER_ID        Is optional, but is strongly recommended in order to make the resultant data files as
                    useful as possible. A Wafer ID in the WRR supersedes any Wafer ID found in the WIR.
    FABWF_ID        Is the ID of the wafer when it was in the fabrication process. This facilitates tracking
                    of wafers and correlation of yield with fabrication variations.
    FRAME_ID        Facilitates tracking of wafers once the wafer has been through the saw step and the
                    wafer ID is no longer readable on the wafer itself. This is an important piece of
                    information for implementing an inkless binning scheme.
    Frequency:      One per wafer tested.
    Location:       Anywhere in the data stream after the corresponding WIR.
                    Sent after testing each wafer.

    Possible Use:   Wafer Summary Sheet         Datalog
                    Wafer Map
    """
    rec_typ = 2
    rec_sub = 20
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_GRP', 'U1'),
        ('FINISH_T', 'U4'),
        ('PART_CNT', 'U4'),
        ('RTST_CNT', 'U4'),
        ('ABRT_CNT', 'U4'),
        ('GOOD_CNT', 'U4'),
        ('FUNC_CNT', 'U4'),
        ('WAFER_ID', 'Cn'),
        ('FABWF_ID', 'Cn'),
        ('FRAME_ID', 'Cn'),
        ('MASK_ID', 'Cn'),
        ('USR_DESC', 'Cn'),
        ('EXC_DESC', 'Cn')
    )

    def __init__(self, HEAD_NUM, FINISH_T, PART_CNT, SITE_GRP=255, RTST_CNT=4294967295, ABRT_CNT=4294967295,
                 GOOD_CNT=4294967295, FUNC_CNT=4294967295, WAFER_ID="", FABWF_ID="", MASK_ID="", FRAME_ID="",
                 USR_DESC="", EXC_DESC=""):
        self.field_values = locals()


class WCR(Record):
    """
    Function: Contains the configuration information for the wafers tested by the job plan. The
                WCR provides the dimensions and orientation information for all wafers and dice
                in the lot. This record is used only when testing at wafer probe time.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (2)
    REC_SUB         U*1             Record sub-type (30)

    WAFR_SIZ        R*4             Diameter of wafer in WF_UNITS           0
    DIE_HT          R*4             Height of die in WF_UNITS               0
    DIE_WID         R*4             Width of die in WF_UNITS                0
    WF_UNITS        U*1             Units for wafer and die dimensions      0
    WF_FLAT         C*1             Orientation of wafer flat               space
    CENTER_X        I*2             X coordinate of center die on wafer     -32768
    CENTER_Y        I*2             Y coordinate of center die on wafer     -32768
    POS_X           C*1             Positive X direction of wafer           space
    POS_Y           C*1             Positive Y direction of wafer           space
    =================================================================================================
    Notes on Specific Fields:
    WF_UNITS        Has these valid values: 0 = Unknown units
                        1 = Units are in inches
                        2 = Units are in centimeters
                        3 = Units are in millimeters
                        4 = Units are in mils
    WF_FLAT         Has these valid values: U = Up
                        D = Down
                        L = Left
                        R = Right
                        space = Unknown
    CENTER_X,
    CENTER_Y        Use the value -32768 to indicate that the field is invalid.
    POS_X           Has these valid values: L = Left
                        R = Right
                        space = Unknown
    POS_Y           Has these valid values: U = Up
                        D = Down
                        space = Unknown
    Frequency:      One per STDF file (used only if wafer testing).
    Location:       Anywhere in the data stream after the initial sequence (see page 14), and before the
                    MRR.

    Possible Use:   Wafer Map
    """
    rec_typ = 2
    rec_sub = 30
    field_names = (
        ('WAFR_SIZ', 'R4'),
        ('DIE_HT', 'R4'),
        ('DIE_WID', 'R4'),
        ('WF_UNITS', 'U1'),
        ('WF_FLAT', 'C1'),
        ('CENTER_X', 'I2'),
        ('CENTER_Y', 'I2'),
        ('POS_X', 'C1'),
        ('POS_Y', 'C1')
    )

    def __init__(self, WAFR_SIZ=0, DIE_HT=0, DIE_WID=0, WF_UNITS=0, WF_FLAT=" ", CENTER_X=-32768,
                 CENTER_Y=-32768, POS_X=" ", POS_Y=" "):
        self.field_values = locals()


class PIR(Record):
    """
    Function: Acts as a marker to indicate where testing of a particular part begins for each part
                tested by the test program. The PIR and the Part Results Record (PRR) bracket all the
                stored information pertaining to one tested part.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (5)
    REC_SUB         U*1             Record sub-type (10)

    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM,
    SITE_NUM        If a test system does not support parallel testing, and does not have a standard way to
                    identify its single test site or head, then these fields should be set to 1.
                    When parallel testing, these fields are used to associate individual datalogged results
                    (FTRs and PTRs) with a PIR/PRR pair. An FTR or PTR belongs to the PIR/PRR pair having
                    the same values for HEAD_NUM and SITE_NUM.
    Frequency:      One per part tested.
    Location:       Anywhere in the data stream after the initial sequence (see page 14), and before the
                    corresponding PRR.
                    Sent before testing each part.

    Possible Use:   Datalog
    """
    rec_typ = 5
    rec_sub = 10
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1')
    )

    def __init__(self, HEAD_NUM, SITE_NUM):
        self.field_values = locals()


class PRR(Record):
    """
    Function: Contains the result information relating to each part tested by the test program. The
                PRR and the Part Information Record (PIR) bracket all the stored information
                pertaining to one tested part.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (5)
    REC_SUB         U*1             Record sub-type (20)

    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    PART_FLG        B*1             Part information flag
    NUM_TEST        U*2             Number of tests executed
    HARD_BIN        U*2             Hardware bin number
    SOFT_BIN        U*2             Software bin number                     65535
    X_COORD         I*2             (Wafer) X coordinate                    -32768
    Y_COORD         I*2             (Wafer) Y coordinate                    -32768
    TEST_T          U*4             Elapsed test time in milliseconds       0
    PART_ID         C*n             Part identification                     length byte = 0
    PART_TXT        C*n             Part description text                   length byte = 0
    PART_FIX        B*n             Part repair information                 length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM,
    SITE_NUM        If a test system does not support parallel testing, and does not have a standard way to
                    identify its single test site or head, then these fields should be set to 1.
                    When parallel testing, these fields are used to associate individual datalogged results
                    (FTRs and PTRs) with a PIR/PRR pair. An FTR or PTR belongs to the PIR/PRR pair having
                    the same values for HEAD_NUM and SITE_NUM.
    X_COORD,
    Y_COORD         Have legal values in the range -32767 to 32767. A missing value is indicated by the
                    value -32768.
    X_COORD,
    Y_COORD,
    PART_ID         Are all optional, but you should provide either the PART_ID or the X_COORD and
                    Y_COORD in order to make the resultant data useful for analysis.
    PART_FLG        Contains the following fields:
                    bit 0: 0 = This is a new part. Its data device does not supersede that of any previous
                                device.
                           1 = The PIR, PTR, MPR, FTR, and PRR records that make up the current
                                sequence (identified as having the same HEAD_NUM and SITE_NUM)
                                supersede any previous sequence of records with the same PART_ID. (A
                                repeated part sequence usually indicates a mistested part.)
                    bit 1: 0 = This is a new part. Its data device does not supersede that of any previous
                                device.
                           1 = The PIR, PTR, MPR, FTR, and PRR records that make up the current
                            sequence (identified as having the same HEAD_NUM and SITE_NUM)
                            supersede any previous sequence of records with the same X_COORD and
                            Y_COORD. (A repeated part sequence usually indicates a mistested part.)
                            Note: Either Bit 0 or Bit 1 can be set, but not both. (It is also valid to have neither
                            set.)
                    bit 2: 0 = Part testing completed normally
                           1 = Abnormal end of testing
                    bit 3: 0 = Part passed
                            1 = Part failed
                    bit 4: 0 = Pass/fail flag (bit 3) is valid
                            1 = Device completed testing with no pass/fail indication (i.e., bit 3 is invalid)
                    bits 5 - 7: Reserved for future use — must be 0
    HARD_BIN        Has legal values in the range 0 to 32767.
    SOFT_BIN        Has legal values in the range 0 to 32767. A missing value is indicated by the value
                    65535.
    PART_FIX        This is an application-specific field for storing device repair information. Itmay be used
                    for bit-encoded, integer, floating point, or character information. Regardless of the
                    information stored, the first byte must contain the number of bytes to follow. This field
                    can be decoded only by an application-specific analysis program. See “Storing Repair
                    Information” on page 75.
    Frequency:      One per part tested.
    Location:       Anywhere in the data stream after the corresponding PIR and before the MRR.
                    Sent after completion of testing each part.

    Possible Use:   Datalog         Wafer map
                    RTBM Shmoo      Plot
                    Repair Data
    """
    rec_typ = 5
    rec_sub = 20
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('PART_FLG', 'B1'),
        ('NUM_TEST', 'U2'),
        ('HARD_BIN', 'U2'),
        ('SOFT_BIN', 'U2'),
        ('X_COORD', 'I2'),
        ('Y_COORD', 'I2'),
        ('TEST_T', 'U4'),
        ('PART_ID', 'Cn'),
        ('PART_TXT', 'Cn'),
        ('PART_FIX', 'Bn')
    )

    def __init__(self, HEAD_NUM, SITE_NUM, PART_FLG, NUM_TEST, HARD_BIN, SOFT_BIN=65535,
                 X_COORD=-32768, Y_COORD=-32768, TEST_T=0, PART_ID="", PART_TXT="", PART_FIX=""):
        self.field_values = locals()


class TSR(Record):
    """
    Function: Contains the test execution and failure counts for one parametric or functional test in
                the test program. Also contains static information, such as test name. The TSR is
                related to the Functional Test Record (FTR), the Parametric Test Record (PTR), and the
                Multiple Parametric Test Record (MPR) by test number, head number, and site
                number.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (10)
    REC_SUB         U*1             Record sub-type (30)

    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    TEST_TYP        C*1             Test type space
    TEST_NUM        U*4             Test number
    EXEC_CNT        U*4             Number of test executions               4,294,967,295
    FAIL_CNT        U*4             Number of test failures                 4,294,967,295
    ALRM_CNT        U*4             Number of alarmed tests                 4,294,967,295
    TEST_NAM        C*n             Test name                               length byte = 0
    SEQ_NAME        C*n             Sequencer (program segment/flow) name   length byte = 0
    TEST_LBL        C*n             Test label or text                      length byte = 0
    OPT_FLAG        B*1             Optional data flag See note
    TEST_TIM        R*4             Average test execution time in seconds  OPT_FLAG bit 2 = 1
    TEST_MIN        R*4             Lowest test result value                OPT_FLAG bit 0 = 1
    TEST_MAX        R*4             Highest test result value               OPT_FLAG bit 1 = 1
    TST_SUMS        R*4             Sum of test result values               OPT_FLAG bit 4 = 1
    TST_SQRS        R*4             Sum of squares of test result values    OPT_FLAG bit 5 = 1
    =================================================================================================
    Notes on Specific Fields:
    HEAD_NUM        If this TSR contains a summary of the test counts for all test sites, this field must be
                    set to 255.
    TEST_TYP        Indicates what type of test this summary data is for. Valid values are:
                        P = Parametric test
                        F = Functional test
                        M = Multiple-result parametric test
                        space = Unknown
    EXEC_CNT,
    FAIL_CNT,
    ALRM_CNT        Are optional, but are strongly recommended because they are needed to compute
                    values for complete final summary sheets.
    OPT_FLAG        Contains the following fields:
                        bit 0 set = TEST_MIN value is invalid
                        bit 1 set = TEST_MAX value is invalid
                        bit 2 set = TEST_TIM value is invalid
                        bit 3 is reserved for future use and must be 1
                        bit 4 set = TST_SUMS value is invalid
                        bit 5 set = TST_SQRS value is invalid
                        bits 6 - 7 are reserved for future use and must be 1
                        OPT_FLAG is optional if it is the last field in the record.
    TST_SUMS,
    TST_SQRS        Are useful in calculating the mean and standard deviation for a single lot or when
                    combining test data from multiple STDF files.
    Frequency:      One for each test executed in the test program.
                    May optionally be used to identify unexecuted tests.
    Location:       Anywhere in the data stream after the initial sequence (see page 14) and before the
                    MRR.
                    When test data is being generated in real-time, these records will appear after the last
                    PRR.

    Possible Use:   Final Summary Sheet         Datalog
                    Merged Summary Sheet        Histogram
                    Wafer Map                   Functional Histogram
    """
    rec_typ = 10
    rec_sub = 30
    field_names = (
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('TEST_TYP', 'C1'),
        ('TEST_NUM', 'U4'),
        ('EXEC_CNT', 'U4'),
        ('FAIL_CNT', 'U4'),
        ('ALRM_CNT', 'U4'),
        ('TEST_NAM', 'Cn'),
        ('SEQ_NAME', 'Cn'),
        ('TEST_LBL', 'Cn'),
        ('OPT_FLAG', 'B1'),
        ('TEST_TIM', 'R4'),
        ('TEST_MIN', 'R4'),
        ('TEST_MAX', 'R4'),
        ('TST_SUMS', 'R4'),
        ('TST_SQRS', 'R4')
    )

    def __init__(self, HEAD_NUM, SITE_NUM, TEST_NUM, OPT_FLAG=0x00, TEST_TYP=" ", EXEC_CNT=4294967295,
                 FAIL_CNT=4294967295, ALRM_CNT=4294967295, TEST_NAM="", SEQ_NAME="", TEST_LBL="",
                 TEST_TIM=-1, TEST_MIN=-1, TEST_MAX=-1, TST_SUMS=-1, TST_SQRS=-1):
        self.field_values = locals()
        # if int(OPT_FLAG) & 1:  # bit 0 is set
        #     self.field_values["TEST_MIN"] = 0
        # if int(OPT_FLAG) & (1 << 1):  # bit 1 is set
        #     self.field_values["TEST_MAX"] = 0
        # if int(OPT_FLAG) & (1 << 2):  # bit 2 is set
        #     self.field_values["TEST_TIM"] = 0
        # if int(OPT_FLAG) & (1 << 4):  # bit 4 is set
        #     self.field_values["TST_SUMS"] = 0
        # if int(OPT_FLAG) & (1 << 5):  # bit 5 is set
        #     self.field_values["TST_SQRS"] = 0


class PTR(Record):
    """
    Function: Contains the results of a single execution of a parametric test in the test program. The
            first occurrence of this record also establishes the default values for all semi-static
            information about the test, such as limits, units, and scaling. The PTR is related to the
            Test Synopsis Record (TSR) by test number, head number, and site number.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (15)
    REC_SUB         U*1             Record sub-type (10)

    TEST_NUM        U*4             Test number
    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    TEST_FLG        B*1             Test flags (fail, alarm, etc.)
    PARM_FLG        B*1             Parametric test flags (drift, etc.)
    RESULT          R*4             Test result                             TEST_FLG bit 1 = 1
    TEST_TXT        C*n             Test description text or label          length byte = 0
    ALARM_ID        C*n             Name of alarm                           length byte = 0
    OPT_FLAG        B*1             Optional data flag See note
    RES_SCAL        I*1             Test results scaling exponent           OPT_FLAG bit 0 = 1
    LLM_SCAL        I*1             Low limit scaling exponent              OPT_FLAG bit 4 or 6 = 1
    HLM_SCAL        I*1             High limit scaling exponent             OPT_FLAG bit 5 or 7 = 1
    LO_LIMIT        R*4             Low test limit value                    OPT_FLAG bit 4 or 6 = 1
    HI_LIMIT        R*4             High test limit value                   OPT_FLAG bit 5 or 7 = 1
    UNITS           C*n             Test units                              length byte = 0
    C_RESFMT        C*n             ANSI C result format string             length byte = 0
    C_LLMFMT        C*n             ANSI C low limit format string          length byte = 0
    C_HLMFMT        C*n             ANSI C high limit format string         length byte = 0
    LO_SPEC         R*4             Low specification limit value           OPT_FLAG bit 2 = 1
    HI_SPEC         R*4             High specification limit value          OPT_FLAG bit 3 = 1
    =================================================================================================
    Notes on Specific Fields:
    Default Data    All data following the OPT_FLAG field has a special function in the STDF file. The first
                    PTR for each test will have these fields filled in. These values will be the default for each
                    subsequent PTR with the same test number: if a subsequent PTR has a value for one of
                    these fields, it will be used instead of the default, for that one record only; if the field is
                    blank, the default will be used. This method replaces use of the PDR in STDF V3.
                    If the PTR is not associated with a test execution (that is, it contains only default
                    information), bit 4 of the TEST_FLG field must be set, and the PARM_FLG field must be
                    zero.
                    Unless the default is being overridden, the default data fields should be omitted in
                    order to save space in the file.
                    Note that RES_SCAL, LLM_SCAL, HLM_SCAL, UNITS, C_RESFMT, C_LLMFMT, and
                    C_HLMFMT are interdependent. If you are overriding the default value of one, make
                    sure that you also make appropriate changes to the others in order to keep them
                    consistent.
                    For character strings, you can override the default with a null value by setting the
                    string length to 1 and the string itself to a single binary 0.
    HEAD_NUM,
    SITE_NUM        If a test system does not support parallel testing, and does not have a standard way of
                    identifying its single test site or head, these fields should be set to 1.
                    When parallel testing, these fields are used to associate individual datalogged results
                    with a PIR/PRR pair. A PTR belongs to the PIR/PRR pair having the same values for
                    HEAD_NUM and SITE_NUM.

    Frequency:      One per parametric test execution.
    Location:       Under normal circumstances, the PTR can appear anywhere in the data stream after
                    the corresponding Part Information Record (PIR) and before the corresponding Part
                    Result Record (PRR).
                    In addition, to facilitate conversion from STDF V3, if the first PTR for a test contains
                    default information only (no test results), it may appear anywhere after the initial
                    sequence (see page 14), and before the first corresponding PTR, but need not appear
                    between a PIR and PRR.

    Possible Use:   Datalog
                    Histogram
                    Wafer Map
    """
    rec_typ = 15
    rec_sub = 10
    field_names = (
        ('TEST_NUM', 'U4'),
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('TEST_FLG', 'B1'),
        ('PARM_FLG', 'B1'),
        ('RESULT', 'R4'),
        ('TEST_TXT', 'Cn'),
        ('ALARM_ID', 'Cn'),
        ('OPT_FLAG', 'B1'),
        ('RES_SCAL', 'I1'),
        ('LLM_SCAL', 'I1'),
        ('HLM_SCAL', 'I1'),
        ('LO_LIMIT', 'R4'),
        ('HI_LIMIT', 'R4'),
        ('UNITS', 'Cn'),
        ('C_RESFMT', 'Cn'),
        ('C_LLMFMT', 'Cn'),
        ('C_HLMFMT', 'Cn'),
        ('LO_SPEC', 'R4'),
        ('HI_SPEC', 'R4')
    )

    def __init__(self, TEST_NUM, HEAD_NUM, SITE_NUM, TEST_FLG, PARM_FLG, RESULT, TEST_TXT="",
                 ALARM_ID="", OPT_FLAG=0x00, RES_SCAL=0, LLM_SCAL=0, HLM_SCAL=0, LO_LIMIT=float('-inf'),
                 HI_LIMIT=float('inf'), UNITS="", C_RESFMT="", C_LLMFMT="", C_HLMFMT="", LO_SPEC=0, HI_SPEC=0):
        self.field_values = locals()


class MPR(Record):
    """
    Function: Contains the results of a single execution of a parametric test in the test program
                where that test returns multiple values. The first occurrence of this record also
                establishes the default values for all semi-static information about the test, such as
                limits, units, and scaling. The MPR is related to the Test Synopsis Record (TSR) by test
                number, head number, and site number

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (15)
    REC_SUB         U*1             Record sub-type (15)

    TEST_NUM        U*4             Test number
    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    TEST_FLG        B*1             Test flags (fail, alarm, etc.)
    PARM_FLG        B*1             Parametric test flags (drift, etc.)
    RTN_ICNT        U*2             Count (j) of PMR indexes See note
    RSLT_CNT        U*2             Count (k) of returned results See note
    RTN_STAT        jxN*1           Array of returned states                RTN_ICNT = 0
    RTN_RSLT        kxR*4           Array of returned results               RSLT_CNT = 0
    TEST_TXT        C*n             Descriptive text or label               length byte = 0
    ALARM_ID        C*n             Name of alarm length byte = 0
    OPT_FLAG        B*1             Optional data flag See note
    RES_SCAL        I*1             Test result scaling exponent            OPT_FLAG bit 0 = 1
    LLM_SCAL        I*1             Test low limit scaling exponent         OPT_FLAG bit 4 or 6 = 1
    HLM_SCAL        I*1             Test high limit scaling exponent        OPT_FLAG bit 5 or 7 = 1
    LO_LIMIT        R*4             Test low limit value                    OPT_FLAG bit 4 or 6 = 1
    HI_LIMIT        R*4             Test high limit value                   OPT_FLAG bit 5 or 7 = 1
    START_IN        R*4             Starting input value (condition)        OPT_FLAG bit 1 = 1
    INCR_IN         R*4             Increment of input condition            OPT_FLAG bit 1 = 1
    RTN_INDX        jxU*2           Array of PMR indexes                    RTN_ICNT = 0
    UNITS           C*n             Units of returned results               length byte = 0
    UNITS_IN        C*n             Input condition units                   length byte = 0
    C_RESFMT        C*n             ANSI C result format string             length byte = 0
    C_LLMFMT        C*n             ANSI C low limit format string          length byte = 0
    C_HLMFMT        C*n             ANSI C high limit format string         length byte = 0
    LO_SPEC         R*4             Low specification limit value           OPT_FLAG bit 2 = 1
    HI_SPEC         R*4             High specification limit value          OPT_FLAG bit 3 = 1
    =================================================================================================
    Notes on Specific Fields:
    Default         Data All data beginning with the OPT_FLAG field has a special function in the STDF file. The
                    first MPR for each test will have these fields filled in. These values will be the default
                    for each subsequent MPR with the same test number: if a subsequent MPR has a value
                    for one of these fields, it will be used instead of the default, for that one record only; if
                    the field is blank, the default will be used.
                    If the MPR is not associated with a test execution (that is, it contains only default
                    information), bit 4 of the TEST_FLG field must be set, and the PARM_FLG field must be
                    zero.
                    Unless the default is being overridden, the default data fields should be omitted in
                    order to save space in the file.
                    Note that RES_SCAL, LLM_SCAL, HLM_SCAL, UNITS, C_RESFMT, C_LLMFMT, and
                    C_HLMFMT are interdependent. If you are overriding the default value of one, make
                    sure that you also make appropriate changes to the others in order to keep them
                    consistent.
                    For character strings, you can override the default with a null value by setting the
                    string length to 1 and the string itself to a single binary 0.
    TEST_NUM        The test number does not implicitly increment for successive values in the result array.
    HEAD_NUM,
    SITE_NUM        If a test system does not support parallel testing, and does not have a standard way of
                    identifying its single test site or head, these fields should be set to 1.
                    When parallel testing, these fields are used to associate individual datalogged results
                    with a PIR/PRR pair. A PTR belongs to the PIR/PRR pair having the same values for
                    HEAD_NUM and SITE_NUM.

    Frequency:      One per multiple-result parametric test execution.
    Location:       Anywhere in the data stream after the corresponding Part Information Record (PIR)
                    and before the corresponding Part Result Record (PRR).

    Possible Use:   Datalog             Shmoo Plot
    """
    rec_typ = 15
    rec_sub = 15
    field_names = (
        ('TEST_NUM', 'U4'),
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('TEST_FLG', 'B1'),
        ('PARM_FLG', 'B1'),
        ('RTN_ICNT', 'U2'),
        ('RSLT_CNT', 'U2'),
        ('RTN_STAT', 'kxN1'),
        ('RTN_RSLT', 'kxR4'),
        ('TEST_TXT', 'Cn'),
        ('ALARM_ID', 'Cn'),
        ('OPT_FLAG', 'B1'),
        ('RES_SCAL', 'I1'),
        ('LLM_SCAL', 'I1'),
        ('HLM_SCAL', 'I1'),
        ('LO_LIMIT', 'R4'),
        ('HI_LIMIT', 'R4'),
        ('START_IN', 'R4'),
        ('INCR_IN', 'R4'),
        ('RTN_INDX', 'kxU2'),
        ('UNITS', 'Cn'),
        ('UNITS_IN', 'Cn'),
        ('C_RESFMT', 'Cn'),
        ('C_LLMFMT', 'Cn'),
        ('C_HLMFMT', 'Cn'),
        ('LO_SPEC', 'R4'),
        ('HI_SPEC', 'R4')
    )

    def __init__(self, TEST_NUM, HEAD_NUM, SITE_NUM, TEST_FLG, PARM_FLG, RTN_ICNT, RSLT_CNT,
                 RTN_STAT=0, RTN_RSLT=0, TEST_TXT="", ALARM_ID="", OPT_FLAG=0x00, RES_SCAL=0,
                 LLM_SCAL=0, HLM_SCAL=0, LO_LIMIT=float('-inf'), HI_LIMIT=float('inf'), START_IN=0,
                 INCR_IN=0, RTN_INDX=0, UNITS="", UNITS_IN="", C_RESFMT="", C_LLMFMT="", C_HLMFMT="",
                 LO_SPEC=float('-inf'), HI_SPEC=float('inf')):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add RTN_STAT length
        self.rec_len += pack_len_map["U1"] * int(self.field_values["RTN_ICNT"] / 2 + self.field_values["RTN_ICNT"] % 2)
        # add RTN_RSLT length
        self.rec_len += pack_len_map["R4"] * self.field_values["RSLT_CNT"]
        # add RTN_INDX length
        self.rec_len += pack_len_map["U2"] * self.field_values["RTN_ICNT"]

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU2":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["RTN_ICNT"])
            elif f[1] == "kxN1":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["RTN_ICNT"])
            elif f[1] == "kxR4":
                write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["RSLT_CNT"])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class FTR(Record):
    """
    Function: Contains the results of the single execution of a functional test in the test program. The
                first occurrence of this record also establishes the default values for all semi-static
                information about the test. The FTR is related to the Test Synopsis Record (TSR) by test
                number, head number, and site number.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (15)
    REC_SUB         U*1             Record sub-type (20)

    TEST_NUM        U*4             Test number
    HEAD_NUM        U*1             Test head number
    SITE_NUM        U*1             Test site number
    TEST_FLG        B*1             Test flags (fail, alarm, etc.)
    OPT_FLAG        B*1             Optional data flag See note
    CYCL_CNT        U*4             Cycle count of vector                   OPT_FLAG bit 0 = 1
    REL_VADR        U*4             Relative vector address                 OPT_FLAG bit 1 = 1
    REPT_CNT        U*4             Repeat count of vector                  OPT_FLAG bit 2 = 1
    NUM_FAIL        U*4             Number of pins with 1 or more failures  OPT_FLAG bit 3 = 1
    XFAIL_AD        I*4             X logical device failure address        OPT_FLAG bit 4 = 1
    YFAIL_AD        I*4             Y logical device failure address        OPT_FLAG bit 4 = 1
    VECT_OFF        I*2             Offset from vector of interest O        PT_FLAG bit 5 = 1
    RTN_ICNT        U*2             Count (j) of return data PMR indexes See note
    PGM_ICNT        U*2             Count (k) of programmed state indexes See note
    RTN_INDX        jxU*2           Array of return data PMR indexes        RTN_ICNT = 0
    RTN_STAT        jxN*1           Array of returned states                RTN_ICNT = 0
    PGM_INDX        kxU*2           Array of programmed state indexes       PGM_ICNT = 0
    PGM_STAT        kxN*1           Array of programmed states              PGM_ICNT = 0
    FAIL_PIN        D*n             Failing pin bitfield                    length bytes = 0
    VECT_NAM        C*n             Vector module pattern name              length byte = 0
    TIME_SET        C*n             Time set name                           length byte = 0
    OP_CODE         C*n             Vector Op Code                          length byte = 0
    TEST_TXT        C*n             Descriptive text or label               length byte = 0
    ALARM_ID        C*n             Name of alarm                           length byte = 0
    PROG_TXT        C*n             Additional programmed information       length byte = 0
    RSLT_TXT        C*n             Additional result information           length byte = 0
    PATG_NUM        U*1             Pattern generator number                255
    SPIN_MAP        D*n             Bit map of enabled comparators          length byte = 0
    =================================================================================================
    Notes on Specific Fields:
    Default Data        All data starting with the PATG_NUM field has a special function in the STDF file. The
                        first FTR for each test will have these fields filled in. These values will be the default
                        for each subsequent FTR with the same test number. If a subsequent FTR has a value
                        for one of these fields, it will be used instead of the default, for that one record only. If
                        the field is blank, the default will be used. Thismethod replaces use of the FDR in STDF
                        V3.
                        Unless the default is being overridden, the default data fields should be omitted in
                        order to save space in the file.
    HEAD_NUM,
    SITE_NUM
                    If a test system does not support parallel testing, and does not have a standard way of
                    identifying its single test site or head, these fields should be set to 1.
                    When parallel testing, these fields are used to associate individual datalogged results
                    with a PIR/PRR pair. An FTR belongs to the PIR/PRR pair having the same values for
                    HEAD_NUM and SITE_NUM.

    Frequency:      One or more for each execution of a functional test.
    Location:       Anywhere in the data stream after the corresponding Part Information Record (PIR)
                    and before the corresponding Part Result Record (PRR).

    Possible Use:   Datalog Functional      Histogram
                    Functional Failure Analyzer
    """
    rec_typ = 15
    rec_sub = 20
    field_names = (
        ('TEST_NUM', 'U4'),
        ('HEAD_NUM', 'U1'),
        ('SITE_NUM', 'U1'),
        ('TEST_FLG', 'B1'),
        ('OPT_FLAG', 'B1'),
        ('CYCL_CNT', 'U4'),
        ('REL_VADR', 'U4'),
        ('REPT_CNT', 'U4'),
        ('NUM_FAIL', 'U4'),
        ('XFAIL_AD', 'I4'),
        ('YFAIL_AD', 'I4'),
        ('VECT_OFF', 'I2'),
        ('RTN_ICNT', 'U2'),
        ('PGM_ICNT', 'U2'),
        ('RTN_INDX', 'kxU2'),
        ('RTN_STAT', 'kxN1'),
        ('PGM_INDX', 'kxU2'),
        ('PGM_STAT', 'kxN1'),
        ('FAIL_PIN', 'Dn'),
        ('VECT_NAM', 'Cn'),
        ('TIME_SET', 'Cn'),
        ('OP_CODE', 'Cn'),
        ('TEST_TXT', 'Cn'),
        ('ALARM_ID', 'Cn'),
        ('PROG_TXT', 'Cn'),
        ('RSLT_TXT', 'Cn'),
        ('PATG_NUM', 'U1'),
        ('SPIN_MAP', 'Dn')
    )

    def __init__(self, TEST_NUM, HEAD_NUM, SITE_NUM, TEST_FLG, RTN_INDX, RTN_STAT, PGM_INDX, PGM_STAT,
                 OPT_FLAG=0x00, CYCL_CNT=0, REL_VADR=0, REPT_CNT=0, NUM_FAIL=0, XFAIL_AD=0, YFAIL_AD=0,
                 VECT_OFF=0, RTN_ICNT=0, PGM_ICNT=0, FAIL_PIN="", VECT_NAM="", TIME_SET="", OP_CODE="",
                 TEST_TXT="", ALARM_ID="", PROG_TXT="", RSLT_TXT="", PATG_NUM=255, SPIN_MAP=""):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add RTN_INDX length
        self.rec_len += pack_len_map["U2"] * self.field_values["RTN_ICNT"]
        # add RTN_STAT length
        self.rec_len += pack_len_map["U1"] * int(self.field_values["RTN_ICNT"] / 2 + self.field_values["RTN_ICNT"] % 2)
        # add PGM_INDX length
        self.rec_len += pack_len_map["U2"] * self.field_values["PGM_ICNT"]
        # add PGM_STAT length
        self.rec_len += pack_len_map["U1"] * int(self.field_values["PGM_ICNT"] / 2 + self.field_values["PGM_ICNT"] % 2)

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == "kxU2":
                if f[0] == "RTN_INDX":
                    write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["RTN_ICNT"])
                elif f[0] == "PGM_INDX":
                    write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["PGM_ICNT"])
            elif f[1] == "kxN1":
                if f[0] == "RTN_STAT":
                    write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["RTN_ICNT"])
                elif f[0] == "PGM_STAT":
                    write_record_map[f[1]](inf, self.field_values[f[0]], self.field_values["PGM_ICNT"])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class BPS(Record):
    """
    Function: Marks the beginning of a new program section (or sequencer) in the job plan.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (20)
    REC_SUB         U*1             Record sub-type (10)

    SEQ_NAME        C*n             Program section (or sequencer) name     length byte = 0
    =================================================================================================
    Frequency:      Optional on each entry into the program segment.
    Location:       Anywhere after the PIR and before the PRR.
    Possible        Use: When performing analyses on a particular program segment’s test.
    """
    rec_typ = 20
    rec_sub = 10
    field_names = (
        ('SEQ_NAME', 'Cn'),
    )

    def __init__(self, SEQ_NAME=""):
        self.field_values = locals()


class EPS(Record):
    """
    Function: Marks the end of the current program section (or sequencer) in the job plan.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (20)
    REC_SUB         U*1             Record sub-type (20)

    =================================================================================================
    Frequency:      Optional on each exit from the program segment.
    Location:       Following the corresponding BPS and before the PRR in the data stream.
    Possible Use:
                    When performing analyses on a particular program segment’s test.
                    Note that pairs of BPS and EPS records can be nested: for example, when one sequencer
                    calls another. In this case, the sequence of records could look like this:
                            BPS         SEQ_NAME = sequence-1
                            BPS         SEQ_NAME = sequence-2
                            EPS         (end of sequence-2)
                            EPS         (end of sequence-1)
                    Because an EPS record does not contain the name of the sequencer, it should be
                    assumed that each EPS record matches the last unmatched BPS record.
    """
    rec_typ = 20
    rec_sub = 20
    field_names = ()

    def __init__(self):
        self.field_values = locals()


class GDR(Record):
    """
    Function: Contains information that does not conform to any other record type defined by the
                STDF specification. Such records are intended to be written under the control of job
                plans executing on the tester. This data may be used for any purpose that the user
                desires.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (50)
    REC_SUB         U*1             Record sub-type (10)

    FLD_CNT         U*2             Count of data fields in record
    GEN_DATA        V*n             Data type code and data for one field
                                    (Repeat GEN_DATA for each data field)
    =================================================================================================
    Notes on Specific Fields:
    GEN_DATA        Is repeated FLD_CNT number of times. Each GEN_DATA field consists of a data type code
                    followed by the actual data. The data type code is the first unsigned byte of the field.
                    Valid data types are:
                        0 = B*0 Special pad field, of length 0 (See note below)
                        1 = U*1 One byte unsigned integer
                        2 = U*2 Two byte unsigned integer
                        3 = U*4 Four byte unsigned integer
                        4 = I*1 One byte signed integer
                        5 = I*2 Two byte signed integer
                        6 = I*4 Four byte signed integer
                        7 = R*4 Four byte floating point number
                        8 = R*8 Eight byte floating point number
                        10 = C*n Variable length ASCII character string
                        (first byte is string length in bytes)
                        11 = B*n Variable length binary data string
                        (first byte is string length in bytes)
                        12 = D*n Bit encoded data
                        (first two bytes of string are length in bits)
                        13 = N*1 Unsigned nibble
    Pad Field (Data Type 0):
                Data type 0, the special pad field, is used to force alignment of following data types in
                the record. In particular, itmust be used to ensure even byte alignment of U*2, U*4,
                I*2, I*4, R*4, and R*8 data types.
                The GDR is guaranteed to begin on an even byte boundary. The GDR header contains
                four bytes. The first GEN_DATA field therefore begins on an even byte boundary. It is
                the responsibility of the designer of a GDR record to provide the pad bytes needed to
                ensure data boundary alignment for the CPU on which it will run.
    Example:    The following table describes a sample GDR that contains three data fields of different
                data types. The assumption is that numeric data of more than one byte must begin on
                an even boundary. Pad bytes will be used to meet this requirement.

                Data    Code    Alignment Requirement
                "AB"    10      A variable-length character string can begin on any byte. This field
                                will contain one data byte, one length byte, and two data bytes, for
                                a total length of 4 bytes. Because this field begins on an even byte,
                                the next field also begins on an even byte.
                255     1       A one-byte numeric value can begin on any byte. This field contains
                                two bytes, so the next field also begins on an even byte.
                510     5       A two-byte numeric value must begin on an even byte. This
                                GEN_DATA fieldwould begin on an even byte; and, because the first
                                byte is the data code, the actual numeric value would begin on an
                                odd byte. This field must therefore be preceded by a pad byte.
                The byte representation for this GDR is as follows. The byte ordering shown here is for
                sample purposes only. The actual data representation differs between CPUs. The byte
                values are shown in hexadecimal. The decimal equivalents are given in the description
                of the bytes.
                Even Byte       Odd Byte        Description (with Decimal Values)
                    0c              00          Number of bytes following the header (12)
                    32              0a          Record type (50); record subtype (10)
                    04              00          Number of data fields (4)
                    0a              02          Character string: code (10) and length (2)
                    41              42          Character string: data bytes (“A” and “B”)
                    01              ff          1-byte integer: code (1) and data (255 = 0xff)
                    00              05          Pad byte (0); code (5) for next field
                    fe              01          2-byte signed integer (510 = 0x01fe)
    Frequency:      A test data file may contain any number of GDRs.
    Location:       Anywhere in the data stream after the initial sequence (see page 14).
    Possible Use:   User-written reports
    """
    rec_typ = 50
    rec_sub = 10
    field_names = (
        ('FLD_CNT', 'U2'),
        ('GEN_DATA', 'Vn')
    )

    def __init__(self, FLD_CNT, GEN_DATA):
        self.field_values = locals()

    def cal_rec_len(self):
        super().cal_rec_len()
        # add GEN_DATA length
        for i in self.field_values["GEN_DATA"]:
            if i == 0:
                pass
            elif i == 1:  # first byte is code, second byte is data, so length is 2
                self.rec_len += 2
            elif i == 2:
                self.rec_len += 3
            elif i == 3:
                self.rec_len += 5
            elif i == 4:
                self.rec_len += 2
            elif i == 5:
                self.rec_len += 3
            elif i == 6:
                self.rec_len += 5
            elif i == 7:
                self.rec_len += 5
            elif i == 8:
                self.rec_len += 9
            elif i == 10:   # first byte is code, second byte is data, so length is Cn length plus code byte length
                self.rec_len += len(self.field_values["GEN_DATA"][i]) + 2
            elif i == 11:
                self.rec_len += len(self.field_values["GEN_DATA"][i]) + 2
            elif i == 12:
                self.rec_len += len(self.field_values["GEN_DATA"][i]) + 3
            elif i == 13:
                self.rec_len += pack_len_map["U1"] * int(self.field_values["GEN_DATA"][i] / 2 + self.field_values["GEN_DATA"][i] % 2) + 1

    def write_record(self, inf):
        self.cal_rec_len()
        write_record_map["Header"](inf, self.rec_len, self.rec_typ, self.rec_sub)
        for f in self.field_names:
            if f[1] == 'Vn':
                for i in self.field_values[f[0]]:
                    write_record_map[f[1]][i](inf, self.field_values[f[0]][i])
            else:
                write_record_map[f[1]](inf, self.field_values[f[0]])


class DTR(Record):
    """
    Function: Contains text information that is to be included in the datalog printout. DTRs may be
                written under the control of a job plan: for example, to highlight unexpected test
                results. They may also be generated by the tester executive software: for example, to
                indicate that the datalog sampling rate has changed. DTRs are placed as comments in
                the datalog listing.

    Data Fields:
    Field Name      Data Type       Field Description                       Missing/Invalid Data Flag
    =================================================================================================
    REC_LEN         U*2             Bytes of data following header
    REC_TYP         U*1             Record type (50)
    REC_SUB         U*1             Record sub-type (30)

    TEXT_DAT        C*n             ASCII text string
    =================================================================================================
    Frequency:      A test data file may contain any number of DTRs.
    Location:       Anywhere in the data stream after the initial sequence (see page 14).
    Possible Use:   Datalog
    """
    rec_typ = 50
    rec_sub = 30
    field_names = (
        ('TEXT_DAT', 'Cn'),
    )

    def __init__(self, TEXT_DAT):
        self.field_values = locals()
