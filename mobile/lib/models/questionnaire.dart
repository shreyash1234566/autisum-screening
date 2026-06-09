// questionnaire.dart
// M-CHAT-R: for children 16-30 months (from mchatscreen.com, free)
// AIIMS INDT-ASD: for children > 30 months (Malhotra et al., PLOS ONE 2019)
// AQ-10: used for UCI dataset model training (Baron-Cohen et al. 2010)

enum QuestionnaireType { mchatR, indtAsd }

class QuestionItem {
  final int id;
  final String questionEn;
  final String questionHi;
  final bool invertScoring; // true → "YES" = atypical (risk point)
  final bool isCritical;    // M-CHAT-R critical items → single fail = medium risk

  const QuestionItem({
    required this.id,
    required this.questionEn,
    required this.questionHi,
    this.invertScoring = false,
    this.isCritical = false,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// M-CHAT-R — 20 items — from mchatscreen.com (Robins et al., 2014)
// Hindi validated: Juneja et al., Indian Pediatrics 2024
// Critical items: 2, 5, 6, 7, 8, 9, 10, 11, 14, 15 (0-indexed from guide)
// Scoring:
//   Questions 2, 5, 12 → YES = atypical (invertScoring = true)
//   All others         → NO  = atypical
//   Score 0-2  → Low risk
//   Score 3-7  → Medium risk (follow-up interview)
//   Score 8-20 → High risk
// ─────────────────────────────────────────────────────────────────────────────
const List<QuestionItem> mchatRQuestions = [
  QuestionItem(
    id: 1,
    questionEn: 'If you point at something across the room, does your child look at it?',
    questionHi: 'अगर आप कमरे के उस पार किसी चीज़ की ओर इशारा करें, तो क्या आपका बच्चा उसे देखता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 2,
    questionEn: 'Have you ever wondered if your child might be deaf?',
    questionHi: 'क्या आपने कभी सोचा है कि आपका बच्चा बहरा हो सकता है?',
    invertScoring: true, // YES = atypical
    isCritical: true,
  ),
  QuestionItem(
    id: 3,
    questionEn: 'Does your child play pretend or make-believe?',
    questionHi: 'क्या आपका बच्चा बनावटी खेल खेलता है?',
  ),
  QuestionItem(
    id: 4,
    questionEn: 'Does your child like climbing on things?',
    questionHi: 'क्या आपका बच्चा चीज़ों पर चढ़ना पसंद करता है?',
  ),
  QuestionItem(
    id: 5,
    questionEn: 'Does your child make unusual finger movements near his/her eyes?',
    questionHi: 'क्या आपका बच्चा आँखों के पास असामान्य उंगली की हरकतें करता है?',
    invertScoring: true, // YES = atypical
    isCritical: true,
  ),
  QuestionItem(
    id: 6,
    questionEn: 'Does your child point with one finger to ask for something or to get help?',
    questionHi: 'क्या आपका बच्चा किसी चीज़ के लिए एक उंगली से इशारा करता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 7,
    questionEn: 'Does your child point with one finger to show you something interesting?',
    questionHi: 'क्या आपका बच्चा एक उंगली से आपको कोई दिलचस्प चीज़ दिखाता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 8,
    questionEn: 'Is your child interested in other children?',
    questionHi: 'क्या आपका बच्चा दूसरे बच्चों में रुचि रखता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 9,
    questionEn: 'Does your child show you things by bringing them to you or holding them up for you to see?',
    questionHi: 'क्या आपका बच्चा आपको चीज़ें लाकर या उठाकर दिखाता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 10,
    questionEn: 'Does your child respond to his/her name when you call?',
    questionHi: 'जब आप नाम लेते हैं, तो क्या आपका बच्चा जवाब देता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 11,
    questionEn: 'When you smile at your child, does he/she smile back at you?',
    questionHi: 'जब आप अपने बच्चे को देखकर मुस्कुराते हैं, तो क्या वह भी मुस्कुराता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 12,
    questionEn: 'Does your child get upset by everyday noises?',
    questionHi: 'क्या आपका बच्चा रोज़मर्रा की आवाज़ों से परेशान होता है?',
    invertScoring: true, // YES = atypical
  ),
  QuestionItem(
    id: 13,
    questionEn: 'Does your child walk?',
    questionHi: 'क्या आपका बच्चा चलता है?',
  ),
  QuestionItem(
    id: 14,
    questionEn: 'Does your child look you in the eye when you are talking or playing?',
    questionHi: 'क्या आपका बच्चा बात करते या खेलते वक्त आपकी आँखों में देखता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 15,
    questionEn: 'Does your child try to copy what you do?',
    questionHi: 'क्या आपका बच्चा आपकी नकल करने की कोशिश करता है?',
    isCritical: true,
  ),
  QuestionItem(
    id: 16,
    questionEn: 'If you turn your head to look at something, does your child look around to see what you are looking at?',
    questionHi: 'अगर आप सिर घुमाकर कुछ देखें, तो क्या आपका बच्चा भी देखने की कोशिश करता है?',
  ),
  QuestionItem(
    id: 17,
    questionEn: 'Does your child try to get you to watch him/her?',
    questionHi: 'क्या आपका बच्चा आपका ध्यान खुद पर लगाने की कोशिश करता है?',
  ),
  QuestionItem(
    id: 18,
    questionEn: 'Does your child understand when you tell him/her to do something?',
    questionHi: 'क्या आपका बच्चा आपकी बात समझता है?',
  ),
  QuestionItem(
    id: 19,
    questionEn: 'If something new happens, does your child look at your face to see how you feel about it?',
    questionHi: 'कुछ नया होने पर क्या बच्चा आपका चेहरा देखता है?',
  ),
  QuestionItem(
    id: 20,
    questionEn: 'Does your child like movement activities?',
    questionHi: 'क्या आपका बच्चा गतिविधि वाले खेल पसंद करता है?',
  ),
];

// ─────────────────────────────────────────────────────────────────────────────
// AIIMS INDT-ASD — 28 items — Malhotra et al., PLOS ONE 2019
// DOI: 10.1371/journal.pone.0213242
// 5-point Likert: 0=Never, 1=Rarely, 2=Sometimes, 3=Often, 4=Always
// Cutoff: total score >= 36 (out of max 112) → ASD concern
// ─────────────────────────────────────────────────────────────────────────────
class LikertItem {
  final int id;
  final String domain;
  final String questionEn;
  final String questionHi;

  const LikertItem({
    required this.id,
    required this.domain,
    required this.questionEn,
    required this.questionHi,
  });
}

const List<LikertItem> indtAsdQuestions = [
  // Domain 1: Social Reciprocity
  LikertItem(id: 1, domain: 'social',
    questionEn: 'Does not respond when his/her name is called',
    questionHi: 'नाम पुकारने पर जवाब नहीं देता'),
  LikertItem(id: 2, domain: 'social',
    questionEn: 'Avoids eye contact during interaction',
    questionHi: 'बातचीत के दौरान आँख से आँख मिलाने से बचता है'),
  LikertItem(id: 3, domain: 'social',
    questionEn: 'Does not share enjoyment by pointing or showing objects',
    questionHi: 'चीज़ें दिखाकर या इशारे से खुशी साझा नहीं करता'),
  LikertItem(id: 4, domain: 'social',
    questionEn: 'Does not smile back when smiled at',
    questionHi: 'मुस्कुराने पर मुस्कुराहट नहीं लौटाता'),
  LikertItem(id: 5, domain: 'social',
    questionEn: 'Does not show interest in other children',
    questionHi: 'दूसरे बच्चों में रुचि नहीं दिखाता'),
  LikertItem(id: 6, domain: 'social',
    questionEn: 'Prefers to play alone rather than with others',
    questionHi: 'दूसरों के साथ खेलने की बजाय अकेले खेलना पसंद करता है'),
  LikertItem(id: 7, domain: 'social',
    questionEn: 'Has difficulty understanding others\' feelings',
    questionHi: 'दूसरों की भावनाएं समझने में कठिनाई होती है'),
  // Domain 2: Communication
  LikertItem(id: 8, domain: 'communication',
    questionEn: 'Speech is delayed compared to peers',
    questionHi: 'हमउम्र बच्चों की तुलना में बोलने में देरी है'),
  LikertItem(id: 9, domain: 'communication',
    questionEn: 'Repeats words or phrases said by others (echolalia)',
    questionHi: 'दूसरों की बात दोहराता है (इकोलालिया)'),
  LikertItem(id: 10, domain: 'communication',
    questionEn: 'Confuses pronouns (uses "you" instead of "I")',
    questionHi: '"मैं" की जगह "तुम" कहता है'),
  LikertItem(id: 11, domain: 'communication',
    questionEn: 'Has unusual or monotone voice quality',
    questionHi: 'आवाज़ असामान्य या एक सुर वाली है'),
  LikertItem(id: 12, domain: 'communication',
    questionEn: 'Difficulty starting or maintaining conversation',
    questionHi: 'बातचीत शुरू करने या जारी रखने में कठिनाई'),
  LikertItem(id: 13, domain: 'communication',
    questionEn: 'Takes language very literally',
    questionHi: 'भाषा को बिल्कुल सीधे अर्थ में लेता है'),
  LikertItem(id: 14, domain: 'communication',
    questionEn: 'Uses unusual or idiosyncratic gestures',
    questionHi: 'असामान्य या अजीब इशारे करता है'),
  // Domain 3: Restricted Repetitive Behaviors
  LikertItem(id: 15, domain: 'repetitive',
    questionEn: 'Flaps hands when excited or upset',
    questionHi: 'उत्साहित या परेशान होने पर हाथ फड़फड़ाता है'),
  LikertItem(id: 16, domain: 'repetitive',
    questionEn: 'Rocks body back and forth',
    questionHi: 'शरीर को आगे-पीछे झुलाता है'),
  LikertItem(id: 17, domain: 'repetitive',
    questionEn: 'Spins objects or self repeatedly',
    questionHi: 'वस्तुओं या खुद को बार-बार घुमाता है'),
  LikertItem(id: 18, domain: 'repetitive',
    questionEn: 'Insists on sameness, upset by small changes in routine',
    questionHi: 'दिनचर्या में छोटे बदलाव से परेशान होता है'),
  LikertItem(id: 19, domain: 'repetitive',
    questionEn: 'Unusual attachment to specific objects',
    questionHi: 'किसी खास वस्तु से असामान्य लगाव'),
  LikertItem(id: 20, domain: 'repetitive',
    questionEn: 'Has very narrow, intense interests',
    questionHi: 'बहुत सीमित और गहरी रुचियाँ हैं'),
  LikertItem(id: 21, domain: 'repetitive',
    questionEn: 'May hurt self (head banging, biting, scratching)',
    questionHi: 'खुद को नुकसान पहुँचा सकता है'),
  // Domain 4: Sensory Processing
  LikertItem(id: 22, domain: 'sensory',
    questionEn: 'Overreacts or underreacts to sounds',
    questionHi: 'आवाज़ों पर अधिक या कम प्रतिक्रिया करता है'),
  LikertItem(id: 23, domain: 'sensory',
    questionEn: 'Overreacts or underreacts to lights',
    questionHi: 'रोशनी पर अधिक या कम प्रतिक्रिया करता है'),
  LikertItem(id: 24, domain: 'sensory',
    questionEn: 'Overreacts or underreacts to touch',
    questionHi: 'स्पर्श पर अधिक या कम प्रतिक्रिया करता है'),
  LikertItem(id: 25, domain: 'sensory',
    questionEn: 'Unusual reactions to taste or smell',
    questionHi: 'स्वाद या गंध पर असामान्य प्रतिक्रिया'),
  LikertItem(id: 26, domain: 'sensory',
    questionEn: 'Seems to have unusually high pain tolerance',
    questionHi: 'दर्द बहुत कम महसूस करता लगता है'),
  LikertItem(id: 27, domain: 'sensory',
    questionEn: 'Unusual response to hot or cold temperature',
    questionHi: 'गर्म या ठंडे तापमान पर असामान्य प्रतिक्रिया'),
  LikertItem(id: 28, domain: 'sensory',
    questionEn: 'Stereotyped or repetitive body movements',
    questionHi: 'शरीर की बार-बार एक जैसी हरकतें'),
];

// Scoring helpers
class QuestionnaireScorer {
  // M-CHAT-R scoring (Robins et al. 2014)
  static Map<String, dynamic> scoreMchatR(Map<int, bool> answers) {
    int totalRisk = 0;
    int criticalFails = 0;

    for (final q in mchatRQuestions) {
      final answer = answers[q.id];
      if (answer == null) continue;

      bool isAtypical;
      if (q.invertScoring) {
        isAtypical = answer == true; // YES = atypical
      } else {
        isAtypical = answer == false; // NO = atypical
      }

      if (isAtypical) {
        totalRisk++;
        if (q.isCritical) criticalFails++;
      }
    }

    String riskLevel;
    if (totalRisk <= 2) {
      riskLevel = 'low';
    } else if (totalRisk <= 7) {
      riskLevel = 'medium';
    } else {
      riskLevel = 'high';
    }

    // Any critical item fail alone = medium risk minimum
    if (criticalFails > 0 && riskLevel == 'low') {
      riskLevel = 'medium';
    }

    // Normalised 0-1 risk score
    final double normScore = totalRisk / 20.0;

    return {
      'total_score': totalRisk,
      'critical_fails': criticalFails,
      'risk_level': riskLevel,
      'normalised_score': normScore,
    };
  }

  // AIIMS INDT-ASD scoring (Malhotra et al. 2019)
  // Cutoff >= 36 out of 112
  static Map<String, dynamic> scoreIndtAsd(Map<int, int> answers) {
    int total = 0;
    for (final q in indtAsdQuestions) {
      total += answers[q.id] ?? 0;
    }

    const int cutoff = 36;
    const int maxScore = 112; // 28 × 4

    final String riskLevel;
    if (total < cutoff * 0.7) {
      riskLevel = 'low';
    } else if (total < cutoff) {
      riskLevel = 'medium';
    } else {
      riskLevel = 'high';
    }

    return {
      'total_score': total,
      'cutoff': cutoff,
      'exceeds_cutoff': total >= cutoff,
      'risk_level': riskLevel,
      'normalised_score': (total / maxScore).clamp(0.0, 1.0),
    };
  }
}
