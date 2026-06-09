// app_strings.dart — Bilingual English / Hindi strings
class AppStrings {
  final String appName;
  final String tagline;
  final String registerChild;
  final String childName;
  final String childAgeMonths;
  final String gender;
  final String male;
  final String female;
  final String other;
  final String language;
  final String english;
  final String hindi;
  final String next;
  final String submit;
  final String back;
  final String consentTitle;
  final String consentBody;
  final String consentAccept;
  final String questionnaireTitle;
  final String yes;
  final String no;
  final String sessionIntroTitle;
  final String sessionIntroBody;
  final String startSession;
  final String taskATitle;
  final String taskBTitle;
  final String taskCTitle;
  final String taskDTitle;
  final String sessionComplete;
  final String uploadingData;
  final String thankYou;
  final String doctorWillReview;
  final String popBubbles;
  final String watchAndCopy;
  final String sitInFront;

  const AppStrings({
    required this.appName,
    required this.tagline,
    required this.registerChild,
    required this.childName,
    required this.childAgeMonths,
    required this.gender,
    required this.male,
    required this.female,
    required this.other,
    required this.language,
    required this.english,
    required this.hindi,
    required this.next,
    required this.submit,
    required this.back,
    required this.consentTitle,
    required this.consentBody,
    required this.consentAccept,
    required this.questionnaireTitle,
    required this.yes,
    required this.no,
    required this.sessionIntroTitle,
    required this.sessionIntroBody,
    required this.startSession,
    required this.taskATitle,
    required this.taskBTitle,
    required this.taskCTitle,
    required this.taskDTitle,
    required this.sessionComplete,
    required this.uploadingData,
    required this.thankYou,
    required this.doctorWillReview,
    required this.popBubbles,
    required this.watchAndCopy,
    required this.sitInFront,
  });
}

const AppStrings englishStrings = AppStrings(
  appName: 'AutiScreen',
  tagline: 'Early Detection · Early Support',
  registerChild: 'Register Child',
  childName: "Child's Name",
  childAgeMonths: 'Age (months)',
  gender: 'Gender',
  male: 'Male',
  female: 'Female',
  other: 'Other',
  language: 'Preferred Language',
  english: 'English',
  hindi: 'Hindi',
  next: 'Next',
  submit: 'Submit',
  back: 'Back',
  consentTitle: 'Before We Begin',
  consentBody:
      'This app records short video clips of your child\'s face during simple activities. '
      'Video is encrypted and stored securely. Only your linked doctor can review it. '
      'This is a screening tool — not a diagnosis. Your doctor makes all clinical decisions. '
      'You can stop the session at any time.',
  consentAccept: 'I Understand and Agree',
  questionnaireTitle: 'About Your Child',
  yes: 'Yes',
  no: 'No',
  sessionIntroTitle: 'Session Setup',
  sessionIntroBody:
      '1. Sit your child in front of the tablet at arm\'s length.\n'
      '2. No other sounds or distractions in the room.\n'
      '3. Press Start, then move behind the tablet.\n'
      '4. The session takes about 8–10 minutes.',
  startSession: 'Start Session',
  taskATitle: 'Watch Together',
  taskBTitle: 'Listening Game',
  taskCTitle: 'Copy Me!',
  taskDTitle: 'Pop the Bubbles!',
  sessionComplete: 'All done!',
  uploadingData: 'Sending data to your doctor securely...',
  thankYou: 'Thank you!',
  doctorWillReview: 'Your doctor will review the results and contact you.',
  popBubbles: 'Pop the bubbles!',
  watchAndCopy: 'Watch and copy what the character does.',
  sitInFront: 'Ask your child to sit in front.',
);

const AppStrings hindiStrings = AppStrings(
  appName: 'AutiScreen',
  tagline: 'जल्दी पहचान · जल्दी सहायता',
  registerChild: 'बच्चे को पंजीकृत करें',
  childName: 'बच्चे का नाम',
  childAgeMonths: 'उम्र (महीनों में)',
  gender: 'लिंग',
  male: 'लड़का',
  female: 'लड़की',
  other: 'अन्य',
  language: 'पसंदीदा भाषा',
  english: 'अंग्रेजी',
  hindi: 'हिंदी',
  next: 'आगे',
  submit: 'जमा करें',
  back: 'वापस',
  consentTitle: 'शुरू करने से पहले',
  consentBody:
      'यह ऐप आपके बच्चे का छोटा वीडियो रिकॉर्ड करता है। '
      'वीडियो सुरक्षित रूप से एन्क्रिप्ट किया जाता है। '
      'केवल आपके डॉक्टर इसे देख सकते हैं। '
      'यह एक स्क्रीनिंग टूल है — निदान नहीं।',
  consentAccept: 'मैं समझता/समझती हूँ और सहमत हूँ',
  questionnaireTitle: 'आपके बच्चे के बारे में',
  yes: 'हाँ',
  no: 'नहीं',
  sessionIntroTitle: 'सत्र की तैयारी',
  sessionIntroBody:
      '1. बच्चे को टैबलेट के सामने बैठाएं।\n'
      '2. कमरे में कोई शोर न हो।\n'
      '3. Start दबाएं, फिर पीछे हट जाएं।\n'
      '4. सत्र लगभग 8–10 मिनट का है।',
  startSession: 'सत्र शुरू करें',
  taskATitle: 'साथ में देखें',
  taskBTitle: 'सुनने का खेल',
  taskCTitle: 'मेरी नकल करो!',
  taskDTitle: 'बुलबुले फोड़ो!',
  sessionComplete: 'हो गया!',
  uploadingData: 'डेटा आपके डॉक्टर को सुरक्षित रूप से भेजा जा रहा है...',
  thankYou: 'धन्यवाद!',
  doctorWillReview: 'आपके डॉक्टर परिणाम की समीक्षा करेंगे और आपसे संपर्क करेंगे।',
  popBubbles: 'बुलबुले फोड़ो!',
  watchAndCopy: 'किरदार जो करे उसकी नकल करो।',
  sitInFront: 'बच्चे को सामने बैठाएं।',
);
