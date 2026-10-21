package com.acadentrix.app.data.local

import com.acadentrix.core.model.AdmissionQuota
import com.acadentrix.core.model.Gender
import com.acadentrix.core.model.InstitutionType
import com.acadentrix.core.model.VerificationStatus
import com.acadentrix.core.validation.ApaarIdValidator
import com.acadentrix.app.data.local.entity.InstitutionEntity
import com.acadentrix.app.data.local.entity.ProgramIntakeEntity
import com.acadentrix.app.data.local.entity.StudentEntity
import kotlin.math.ceil
import kotlin.random.Random

/**
 * Deterministic, offline seed of the national APAAR registry.
 *
 * The dataset models a representative pan-India sample — engineering, management
 * and polytechnic institutes — and deliberately embeds edge-case anomalies so the
 * detection engine has something real to find:
 *  - a cross-institutional duplicate APAAR ID (same person, two states),
 *  - over-admission beyond sanctioned intake,
 *  - NRI and TFW supernumerary ceilings exceeded,
 *  - invalid / placeholder APAAR identifiers,
 *  - foreign nationals without passport documentation,
 *  - enrolment into an unsanctioned programme code.
 */
object SeedData {

    private const val SEED = 20_240_815L
    private const val ACADEMIC_YEAR = "2024-25"

    // ------------------------------------------------------------ institutions

    val institutions: List<InstitutionEntity> = listOf(
        InstitutionEntity(
            institutionId = "1-332491024",
            name = "National Institute of Technology & Management",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Maharashtra",
            city = "Pune",
            affiliationUniversity = "Savitribai Phule Pune University",
            approvalYear = 1996,
            naacGrade = "A++"
        ),
        InstitutionEntity(
            institutionId = "1-338490112",
            name = "Delhi Technological Institute",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Delhi",
            city = "New Delhi",
            affiliationUniversity = "University of Delhi",
            approvalYear = 2003,
            naacGrade = "A+"
        ),
        InstitutionEntity(
            institutionId = "1-245023901",
            name = "College of Engineering Pune",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Maharashtra",
            city = "Pune",
            affiliationUniversity = "Savitribai Phule Pune University",
            approvalYear = 2009,
            naacGrade = "A"
        ),
        InstitutionEntity(
            institutionId = "1-401290033",
            name = "Sri Venkateswara Institute of Technology",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Andhra Pradesh",
            city = "Tirupati",
            affiliationUniversity = "Yogi Vemana University",
            approvalYear = 2001,
            naacGrade = "A++"
        ),
        InstitutionEntity(
            institutionId = "1-677341208",
            name = "Madras Institute of Technology",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Tamil Nadu",
            city = "Chennai",
            affiliationUniversity = "Anna University",
            approvalYear = 1989,
            naacGrade = "A+"
        ),
        InstitutionEntity(
            institutionId = "1-812340567",
            name = "Indian Institute of Technology Madras",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Tamil Nadu",
            city = "Chennai",
            affiliationUniversity = "IIT Madras",
            approvalYear = 1959,
            naacGrade = "A++"
        ),
        InstitutionEntity(
            institutionId = "1-933451208",
            name = "Birla Institute of Technology & Science",
            institutionType = InstitutionType.ENGINEERING.name,
            state = "Rajasthan",
            city = "Pilani",
            affiliationUniversity = "BITS Pilani",
            approvalYear = 1964,
            naacGrade = "A++"
        ),
        InstitutionEntity(
            institutionId = "1-128456772",
            name = "Indian Institute of Management Indore",
            institutionType = InstitutionType.MANAGEMENT.name,
            state = "Madhya Pradesh",
            city = "Indore",
            affiliationUniversity = "IIM Indore",
            approvalYear = 1961,
            naacGrade = "A++"
        ),
        InstitutionEntity(
            institutionId = "1-472908315",
            name = "National Institute of Management Studies",
            institutionType = InstitutionType.MANAGEMENT.name,
            state = "Telangana",
            city = "Hyderabad",
            affiliationUniversity = "Osmania University",
            approvalYear = 2007,
            naacGrade = "A"
        ),
        InstitutionEntity(
            institutionId = "1-155670342",
            name = "Symbiosis Institute of Management Studies",
            institutionType = InstitutionType.MANAGEMENT.name,
            state = "Maharashtra",
            city = "Pune",
            affiliationUniversity = "Symbiosis International University",
            approvalYear = 2002,
            naacGrade = "A+"
        ),
        InstitutionEntity(
            institutionId = "1-550012934",
            name = "Government Polytechnic College",
            institutionType = InstitutionType.POLYTECHNIC.name,
            state = "Uttar Pradesh",
            city = "Kanpur",
            affiliationUniversity = "Uttar Pradesh Technical University",
            approvalYear = 1956,
            naacGrade = "B++"
        ),
        InstitutionEntity(
            institutionId = "1-789023415",
            name = "Aligarh Polytechnic Institute",
            institutionType = InstitutionType.POLYTECHNIC.name,
            state = "Uttar Pradesh",
            city = "Aligarh",
            affiliationUniversity = "Uttar Pradesh Technical University",
            approvalYear = 1994,
            naacGrade = "B+"
        )
    )

    // ------------------------------------------------------------- programmes

    /**
     * Seed description of one programme and its realised enrolment.
     */
    data class ProgramSeed(
        val institutionId: String,
        val programId: String,
        val programName: String,
        val programLevel: String,
        val approvedIntake: Int,
        val enrolled: Int,
        val nri: Int? = null,
        val ociFn: Int? = null,
        val tfw: Int? = null
    )

    val programSeeds: List<ProgramSeed> = listOf(
        // National Institute of Technology & Management, Pune
        ProgramSeed("1-332491024", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 120, 112),
        ProgramSeed("1-332491024", "BTECH_ECE", "B.Tech in Electronics & Communication", "UG", 60, 55),
        ProgramSeed("1-332491024", "MBA_FIN", "Master of Business Administration (Finance)", "PG", 60, 58),

        // Delhi Technological Institute — deliberate over-admission + TFW breach
        ProgramSeed("1-338490112", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 120, 132, tfw = 9),
        ProgramSeed("1-338490112", "BTECH_MECH", "B.Tech in Mechanical Engineering", "UG", 60, 54),
        ProgramSeed("1-338490112", "MCA", "Master of Computer Applications", "PG", 30, 29),

        // College of Engineering Pune — hosts the cross-institution duplicate
        ProgramSeed("1-245023901", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 60, 64),
        ProgramSeed("1-245023901", "BTECH_MECH", "B.Tech in Mechanical Engineering", "UG", 60, 57),
        ProgramSeed("1-245023901", "BTECH_CIVIL", "B.Tech in Civil Engineering", "UG", 60, 51),

        // Sri Venkateswara Institute of Technology
        ProgramSeed("1-401290033", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 60, 59),
        ProgramSeed("1-401290033", "BTECH_ECE", "B.Tech in Electronics & Communication", "UG", 60, 52),

        // Madras Institute of Technology
        ProgramSeed("1-677341208", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 60, 60),
        ProgramSeed("1-677341208", "BTECH_ECE", "B.Tech in Electronics & Communication", "UG", 60, 56),
        ProgramSeed("1-677341208", "MBA_FIN", "Master of Business Administration (Finance)", "PG", 60, 49),

        // IIT Madras
        ProgramSeed("1-812340567", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 120, 118),
        ProgramSeed("1-812340567", "MTECH_BT", "M.Tech in Biotechnology", "PG", 30, 27),

        // BITS Pilani
        ProgramSeed("1-933451208", "BTECH_CSE", "B.Tech in Computer Science & Engineering", "UG", 120, 110),
        ProgramSeed("1-933451208", "BTECH_ECE", "B.Tech in Electronics & Communication", "UG", 60, 57),

        // IIM Indore
        ProgramSeed("1-128456772", "MBA_FIN", "Master of Business Administration (Finance)", "PG", 366, 341),
        ProgramSeed("1-128456772", "MBA_MKT", "Master of Business Administration (Marketing)", "PG", 180, 168),
        ProgramSeed("1-128456772", "PGP_OB", "Post Graduate Programme in Organisational Behaviour", "PG", 120, 109),

        // NIMS Hyderabad
        ProgramSeed("1-472908315", "MBA_FIN", "Master of Business Administration (Finance)", "PG", 120, 116),
        ProgramSeed("1-472908315", "MBA_HR", "Master of Business Administration (Human Resources)", "PG", 60, 55),

        // SIBM Pune — deliberate NRI supernumerary breach
        ProgramSeed("1-155670342", "MBA_FIN", "Master of Business Administration (Finance)", "PG", 180, 172, nri = 12),
        ProgramSeed("1-155670342", "MBA_RHR", "Master of Business Administration (Rural & Healthcare)", "PG", 60, 58),

        // Government Polytechnic College, Kanpur
        ProgramSeed("1-550012934", "DIPLOMA_CSE", "Diploma in Computer Science & Engineering", "DIPLOMA", 60, 54),
        ProgramSeed("1-550012934", "DIPLOMA_MECH", "Diploma in Mechanical Engineering", "DIPLOMA", 60, 47),

        // Aligarh Polytechnic Institute
        ProgramSeed("1-789023415", "DIPLOMA_CSE", "Diploma in Computer Science & Engineering", "DIPLOMA", 60, 58),
        ProgramSeed("1-789023415", "DIPLOMA_ELE", "Diploma in Electronics & Telecommunication", "DIPLOMA", 60, 53)
    )

    fun programs(): List<ProgramIntakeEntity> = programSeeds.map { seed ->
        val nriCap = ceil(seed.approvedIntake * 0.05).toInt().coerceAtLeast(1)
        val fnOciCap = ceil(seed.approvedIntake * 0.15).toInt().coerceAtLeast(1)
        val tfwCap = ceil(seed.approvedIntake * 0.05).toInt().coerceAtLeast(1)
        val pmsssCap = ceil(seed.approvedIntake * 0.05).toInt().coerceAtLeast(1)
        ProgramIntakeEntity(
            institutionId = seed.institutionId,
            programId = seed.programId,
            programName = seed.programName,
            programLevel = seed.programLevel,
            approvedIntake = seed.approvedIntake,
            maxSupernumeraryNri = nriCap,
            maxSupernumeraryFnOci = fnOciCap,
            maxSupernumeraryTfw = tfwCap,
            maxPmsss = pmsssCap
        )
    }

    // --------------------------------------------------------------- students

    private val maleNames = listOf(
        "Aarav", "Vihaan", "Arjun", "Rohan", "Kabir", "Ishaan", "Aditya", "Karan", "Rahul", "Vikram",
        "Siddharth", "Aniket", "Manish", "Pranav", "Yash", "Nikhil", "Saurabh", "Varun", "Harsh", "Devansh",
        "Rishi", "Akhil", "Jay", "Kartik", "Naveen", "Sameer", "Tarun", "Vivek", "Zoya", "Imran",
        "Faisal", "Ayaan", "Rudra", "Neel", "Parth", "Rehan", "Omkar", "Tanmay", "Gaurav", "Abhishek"
    )

    private val femaleNames = listOf(
        "Aanya", "Diya", "Saanvi", "Ishita", "Priya", "Neha", "Ananya", "Riya", "Sneha", "Pooja",
        "Kavya", "Meera", "Anjali", "Shreya", "Nandini", "Divya", "Aditi", "Sanjana", "Tanvi", "Rashi",
        "Swara", "Nisha", "Payal", "Harshita", "Aishwarya", "Bhavana", "Chitra", "Deepika", "Ekta", "Falguni",
        "Gauri", "Hina", "Indira", "Jaya", "Kiran", "Lakshmi", "Manasi", "Nandita", "Ojaswi", "Prisha",
        "Rukmini", "Seema", "Trisha", "Usha", "Vasudha", "Yashika", "Zoya"
    )

    private val lastNames = listOf(
        "Verma", "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Nair", "Iyer", "Gupta", "Mehta",
        "Joshi", "Desai", "Kulkarni", "Chatterjee", "Banerjee", "Mukherjee", "Rao", "Naidu", "Reddy", "Menon",
        "Pillai", "Shetty", "Hegde", "Chauhan", "Yadav", "Malhotra", "Kapoor", "Bose", "Ghosh", "Sen",
        "Prasad", "Rathore", "Thakur", "Choudhary", "Sinha", "Agarwal", "Bansal", "Mishra", "Pandey", "Tiwari",
        "Sethi", "Bhatt", "Shah", "Trivedi", "Solanki", "Rathore", "Khatri", "Saini"
    )

    private val foreignCountries = listOf(
        "Oman", "Qatar", "United Arab Emirates", "Singapore", "United States", "Japan", "Germany", "Canada",
        "United Kingdom", "Australia"
    )

    private val nriCountries = listOf(
        "United Arab Emirates", "United States", "Singapore", "Qatar", "United Kingdom", "Oman", "Kuwait"
    )

    private val rollPrefix = mapOf(
        "BTECH_CSE" to "CSE",
        "BTECH_ECE" to "ECE",
        "BTECH_MECH" to "MEC",
        "BTECH_CIVIL" to "CIV",
        "MCA" to "MCA",
        "MBA_FIN" to "MBA",
        "MBA_MKT" to "MKT",
        "MBA_HR" to "HRM",
        "MBA_RHR" to "RHR",
        "PGP_OB" to "OBP",
        "MTECH_BT" to "BT",
        "DIPLOMA_CSE" to "DCS",
        "DIPLOMA_MECH" to "DME",
        "DIPLOMA_ELE" to "DEL"
    )

    fun students(): List<StudentEntity> {
        val random = Random(SEED)
        val out = mutableListOf<StudentEntity>()
        var counter = 0L

        programSeeds.forEach { seed ->
            val caps = programs().first {
                it.institutionId == seed.institutionId && it.programId == seed.programId
            }
            val nriCount = seed.nri ?: minOf(caps.maxSupernumeraryNri, kotlin.math.round(seed.enrolled * 0.05f).toInt())
            val ociFnCount = seed.ociFn ?: minOf(caps.maxSupernumeraryFnOci, kotlin.math.round(seed.enrolled * 0.10f).toInt())
            val tfwCount = seed.tfw ?: minOf(caps.maxSupernumeraryTfw, kotlin.math.round(seed.enrolled * 0.03f).toInt())
            val supernumerary = nriCount + ociFnCount + tfwCount
            val regular = (seed.enrolled - supernumerary).coerceAtLeast(0)
            val pmsssCount = minOf(caps.maxPmsss, kotlin.math.round(regular * 0.06f).toInt())
            val meritCount = kotlin.math.round((regular - pmsssCount) * 0.88f).toInt()
            val managementCount = (regular - pmsssCount - meritCount).coerceAtLeast(0)

            val quotas = mutableListOf<AdmissionQuota>()
            repeat(meritCount) { quotas += AdmissionQuota.MERIT }
            repeat(managementCount) { quotas += AdmissionQuota.MANAGEMENT }
            repeat(pmsssCount) { quotas += AdmissionQuota.PMSSS }
            repeat(nriCount) { quotas += AdmissionQuota.NRI }
            repeat(ociFnCount) { quotas += if (random.nextBoolean()) AdmissionQuota.OCI else AdmissionQuota.FN }
            repeat(tfwCount) { quotas += AdmissionQuota.TFW }
            quotas.shuffle(random)

            val prefix = rollPrefix[seed.programId] ?: seed.programId.take(3)
            val isPostGraduate = seed.programLevel == "PG"

            quotas.forEachIndexed { index, quota ->
                val isFemale = random.nextInt(100) < 44
                val firstName = if (isFemale) femaleNames.random(random) else maleNames.random(random)
                val lastName = lastNames.random(random)
                val gender = if (isFemale) Gender.FEMALE else Gender.MALE
                val birthYear = if (isPostGraduate) random.nextInt(1998, 2003) else random.nextInt(2003, 2007)
                val birthMonth = random.nextInt(1, 13)
                val birthDay = random.nextInt(1, 29)
                val enrollMonth = random.nextInt(6, 10)
                val enrollDay = random.nextInt(1, 29)

                val nationality = when (quota) {
                    AdmissionQuota.FN -> foreignCountries.random(random)
                    AdmissionQuota.NRI -> "Indian"
                    AdmissionQuota.OCI -> "Indian"
                    else -> "Indian"
                }
                val countryOfOrigin = when (quota) {
                    AdmissionQuota.FN -> nationality
                    AdmissionQuota.NRI -> nriCountries.random(random)
                    AdmissionQuota.OCI -> nriCountries.random(random)
                    else -> null
                }
                val passport = when (quota) {
                    AdmissionQuota.FN -> "P" + (random.nextInt(100000, 999999))
                    AdmissionQuota.NRI -> "P" + (random.nextInt(100000, 999999))
                    AdmissionQuota.OCI -> null
                    else -> null
                }
                val visa = when (quota) {
                    AdmissionQuota.FN -> "31-12-${random.nextInt(2026, 2029)}"
                    AdmissionQuota.NRI -> "31-12-${random.nextInt(2026, 2029)}"
                    else -> null
                }

                counter++
                out += StudentEntity(
                    apaarId = ApaarIdValidator.generate(SEED + counter * 7919L),
                    studentName = "$firstName $lastName",
                    dateOfBirth = "%04d-%02d-%02d".format(birthYear, birthMonth, birthDay),
                    gender = gender.name,
                    institutionId = seed.institutionId,
                    programId = seed.programId,
                    academicYear = ACADEMIC_YEAR,
                    admissionQuota = quota.name,
                    enrollmentDate = "2024-%02d-%02d".format(enrollMonth, enrollDay),
                    studentInstituteRollNo = "$prefix-24-${(index + 1).toString().padStart(3, '0')}",
                    nationality = nationality,
                    passportNumber = passport,
                    visaValidity = visa,
                    countryOfOrigin = countryOfOrigin,
                    abcAccountId = "ABC" + random.nextLong(1_000_000_000L, 9_999_999_999L).toString(),
                    verificationStatus = VerificationStatus.PENDING_REVIEW.name,
                    isActive = true,
                    photoSeed = (counter % 6).toInt()
                )
            }
        }

        out += injectAnomalies(out, random)
        return out
    }

    /**
     * Crafts the deliberate edge cases that the detection engine must catch.
     */
    private fun injectAnomalies(base: List<StudentEntity>, random: Random): List<StudentEntity> {
        val out = base.toMutableList()
        var nextId = 9_000_001L

        fun pick(programId: String, institutionId: String, index: Int): StudentEntity? =
            base.firstOrNull { it.programId == programId && it.institutionId == institutionId && it.admissionQuota == "MERIT" }
                ?.let { base.filter { it.programId == programId && it.institutionId == institutionId }.getOrNull(index) }

        // 1. Cross-institutional duplicate: the same APAAR ID claimed in two states.
        val source = pick("BTECH_CSE", "1-245023901", 0)
        if (source != null) {
            out += source.copy(
                recordId = 0,
                institutionId = "1-338490112",
                programId = "BTECH_CSE",
                studentInstituteRollNo = "CSE-24-901",
                enrollmentDate = "2024-08-11"
            )
        }

        // 2. Invalid / placeholder APAAR identifiers.
        listOf("111111111111", "123456789012", "9842103578").forEachIndexed { index, badId ->
            val template = pick("BTECH_CSE", "1-332491024", index) ?: return@forEachIndexed
            out += template.copy(
                recordId = 0,
                apaarId = badId,
                studentName = if (index == 0) "Ganesh Kumar" else template.studentName,
                studentInstituteRollNo = "CSE-24-95${index}"
            )
        }

        // 3. Foreign national admitted without passport documentation.
        out.indices.forEach { index ->
            val student = out[index]
            if (student.admissionQuota == AdmissionQuota.FN.name && student.institutionId == "1-550012934") {
                out[index] = student.copy(passportNumber = null)
            }
        }

        // 4. Enrolment into a programme code the institution is not approved to offer.
        val unsanctionedTemplate = pick("BTECH_CSE", "1-812340567", 3)
        if (unsanctionedTemplate != null) {
            nextId++
            out += unsanctionedTemplate.copy(
                recordId = 0,
                programId = "BTECH_AI_ML",
                studentInstituteRollNo = "AIM-24-001",
                admissionQuota = AdmissionQuota.MERIT.name
            )
        }

        // 5. A dormant (historic) enrolment that must not be counted as active.
        val dormant = pick("MBA_FIN", "1-128456772", 1)
        if (dormant != null) {
            out += dormant.copy(
                recordId = 0,
                academicYear = "2021-22",
                enrollmentDate = "2021-08-05",
                isActive = false,
                studentInstituteRollNo = "MBA-21-002"
            )
        }

        return out
    }
}
