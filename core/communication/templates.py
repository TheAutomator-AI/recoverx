from typing import Dict, Tuple
from core.domain.enums import Language, Script, Tone

# Structured Multilingual Templates (Language, Script, Tone) -> (Headline, BodyTemplate, CtaTemplate)
TEMPLATES: Dict[Tuple[Language, Script, Tone], Dict[str, str]] = {
    # --- English ---
    (Language.ENGLISH, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "We couldn't process your payment for Order #{order_id}",
        "body": "Hi {name}, we noticed that your payment of ₹{amount:,.2f} for Order #{order_id} could not go through due to a temporary bank response ({reason}). Don't worry, your order is safely reserved for you.",
        "cta": "Retry Payment Securely",
    },
    (Language.ENGLISH, Script.LATIN, Tone.PROFESSIONAL): {
        "headline": "Payment Notice: Order #{order_id}",
        "body": "Dear {name}, the transaction of ₹{amount:,.2f} for Order #{order_id} was unsuccessful ({reason}). Please use the secure link below to re-attempt or update your payment method.",
        "cta": "Complete Payment",
    },
    (Language.ENGLISH, Script.LATIN, Tone.URGENT): {
        "headline": "Action Needed: Order #{order_id} payment pending",
        "body": "Hi {name}, your transaction of ₹{amount:,.2f} requires attention to avoid automatic order release. Please retry now using your preferred UPI app or card.",
        "cta": "Pay Now & Secure Order",
    },
    (Language.ENGLISH, Script.LATIN, Tone.CASUAL): {
        "headline": "Quick heads up on Order #{order_id}!",
        "body": "Hey {name}, looks like the bank had a quick hiccup for your ₹{amount:,.2f} payment. Tap below to finish up in seconds!",
        "cta": "Quick Pay via UPI",
    },

    # --- Hindi (Devanagari) ---
    (Language.HINDI, Script.DEVANAGARI, Tone.EMPATHETIC): {
        "headline": "ऑर्डर #{order_id} के भुगतान में अस्थायी रुकावट",
        "body": "नमस्ते {name} जी, आपके ऑर्डर #{order_id} के लिए ₹{amount:,.2f} का भुगतान बैंक की तकनीकी वजह ({reason}) से पूरा नहीं हो पाया। आपकी सुरक्षा के लिए ऑर्डर सुरक्षित रखा गया है।",
        "cta": "सुरक्षित भुगतान पुनः करें",
    },
    (Language.HINDI, Script.DEVANAGARI, Tone.PROFESSIONAL): {
        "headline": "भुगतान सूचना: ऑर्डर #{order_id}",
        "body": "प्रिय {name}, आपके ऑर्डर #{order_id} के ₹{amount:,.2f} का लेनदेन अस्वीकार हो गया ({reason})। कृपया नीचे दिए गए लिंक से भुगतान पूरा करें।",
        "cta": "भुगतान पूर्ण करें",
    },
    (Language.HINDI, Script.DEVANAGARI, Tone.URGENT): {
        "headline": "आवश्यक: ऑर्डर #{order_id} का भुगतान लंबित है",
        "body": "नमस्ते {name}, ऑर्डर रद्द होने से बचाने के लिए ₹{amount:,.2f} का भुगतान कृपया तुरंत पुनः करें।",
        "cta": "अभी तुरंत भुगतान करें",
    },
    (Language.HINDI, Script.DEVANAGARI, Tone.CASUAL): {
        "headline": "ऑर्डर #{order_id} का पेमेंट रुका है!",
        "body": "अरे {name}, बैंक की तरफ से ₹{amount:,.2f} का पेमेंट पूरा नहीं हो सका। बस एक क्लिक में UPI से पेमेंट पूरा करें!",
        "cta": "UPI से अभी पे करें",
    },

    # --- Hinglish (Hindi in Latin Script) ---
    (Language.HINDI, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} ka payment complete nahi ho paya",
        "body": "Namaste {name}, aapke Order #{order_id} ka ₹{amount:,.2f} ka payment bank technical issue ({reason}) ki wajah se pura nahi ho saka. Aapka order safely reserved hai.",
        "cta": "Securely Retry Karein",
    },
    (Language.HINDI, Script.LATIN, Tone.PROFESSIONAL): {
        "headline": "Payment Notice: Order #{order_id}",
        "body": "Dear {name}, aapka ₹{amount:,.2f} ka payment transaction unsuccesful raha ({reason}). Kripya niche diye link par click karke payment complete karein.",
        "cta": "Complete Payment",
    },
    (Language.HINDI, Script.LATIN, Tone.URGENT): {
        "headline": "Important: Order #{order_id} payment pending",
        "body": "Hi {name}, order cancellation se bachne ke liye ₹{amount:,.2f} ka payment turant re-attempt karein.",
        "cta": "Abhi Pay Karein",
    },
    (Language.HINDI, Script.LATIN, Tone.CASUAL): {
        "headline": "Order #{order_id} payment update!",
        "body": "Hey {name}, bank se ₹{amount:,.2f} ka payment clear nahi hua. Tap karke UPI se jaldi complete kar lo!",
        "cta": "Quick Pay via UPI",
    },

    # --- Tamil (Tamil Script) ---
    (Language.TAMIL, Script.TAMIL, Tone.EMPATHETIC): {
        "headline": "ஆர்டர் #{order_id}க்கான கட்டணம் செலுத்த முடியவில்லை",
        "body": "வணக்கம் {name}, ஆர்டர் #{order_id}க்கான ₹{amount:,.2f} கட்டணம் வங்கி தொழில்நுட்பக் காரணத்தால் ({reason}) தோல்வியடைந்தது. உங்கள் ஆர்டர் பாதுகாப்பாக உள்ளது.",
        "cta": "மீண்டும் பாதுகாப்பாக செலுத்துங்கள்",
    },
    (Language.TAMIL, Script.TAMIL, Tone.PROFESSIONAL): {
        "headline": "கட்டண அறிவிப்பு: ஆர்டர் #{order_id}",
        "body": "அன்புள்ள {name}, ஆர்டர் #{order_id}க்கான ₹{amount:,.2f} பரிவர்த்தனை தோல்வியடைந்தது ({reason}). தயவுசெய்து கீழே உள்ள இணைப்பு மூலம் முடிக்கவும்.",
        "cta": "கட்டணத்தை முடிக்கவும்",
    },
    (Language.TAMIL, Script.TAMIL, Tone.URGENT): {
        "headline": "முக்கியமானது: ஆர்டர் #{order_id} கட்டணம் நிலுவையில் உள்ளது",
        "body": "வணக்கம் {name}, ஆர்டர் ரத்தாவதைத் தவிர்க்க ₹{amount:,.2f} கட்டணத்தை உடனடியாக செலுத்துங்கள்.",
        "cta": "உடனடியாக செலுத்தவும்",
    },
    (Language.TAMIL, Script.TAMIL, Tone.CASUAL): {
        "headline": "ஆர்டர் #{order_id} கட்டணத் தகவல்!",
        "body": "ஹாய் {name}, உங்கள் ₹{amount:,.2f} கட்டணம் வங்கியால் முடிக்கப்படவில்லை. UPI மூலம் உடனே செலுத்தி முடிக்கவும்!",
        "cta": "UPI மூலம் செலுத்தவும்",
    },

    # --- Tanglish (Tamil in Latin Script) ---
    (Language.TAMIL, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} payment complete aagala",
        "body": "Vanakkam {name}, unga Order #{order_id}-kaga ₹{amount:,.2f} payment bank issue ({reason}) nala proceed aagala. Unga order safely reserved aagi irukku.",
        "cta": "Marubadiyum Secure-ah Pay Pannunga",
    },
    (Language.TAMIL, Script.LATIN, Tone.PROFESSIONAL): {
        "headline": "Payment Notice: Order #{order_id}",
        "body": "Dear {name}, unga Order #{order_id}-kaga ₹{amount:,.2f} transaction complete aagala ({reason}). Keela irukkura link use panni payment complete pannunga.",
        "cta": "Payment Complete Pannunga",
    },
    (Language.TAMIL, Script.LATIN, Tone.URGENT): {
        "headline": "Urgent: Order #{order_id} payment pending",
        "body": "Hi {name}, order cancel aaguratha thavirkka ₹{amount:,.2f} payment-ah ippove retry pannunga.",
        "cta": "Ippove Pay Pannunga",
    },
    (Language.TAMIL, Script.LATIN, Tone.CASUAL): {
        "headline": "Order #{order_id} payment quick update!",
        "body": "Hey {name}, bank-la ₹{amount:,.2f} payment fail aaiduchu. Click panni UPI la fast-ah complete pannidunga!",
        "cta": "UPI Moolam Pay Pannunga",
    },

    # --- Telugu (Telugu Script) ---
    (Language.TELUGU, Script.TELUGU, Tone.EMPATHETIC): {
        "headline": "ఆర్డర్ #{order_id} చెల్లింపు పూర్తి కాలేదు",
        "body": "నమస్కారం {name}, మీ ఆర్డర్ #{order_id} కోసం ₹{amount:,.2f} చెల్లింపు బ్యాంక్ సాంకేతిక సమస్య ({reason}) వలన విఫలమైంది. మీ ఆర్డర్ సురక్షితంగా రిజర్వ్ చేయబడింది.",
        "cta": "సురక్షితంగా మళ్ళీ చెల్లించండి",
    },
    (Language.TELUGU, Script.TELUGU, Tone.PROFESSIONAL): {
        "headline": "చెల్లింపు సమాచారం: ఆర్డర్ #{order_id}",
        "body": "ప్రియమైన {name}, ఆర్డర్ #{order_id} కోసం ₹{amount:,.2f} లావాదేవీ విఫలమైంది ({reason}). దయచేసి క్రింది లింక్ ద్వారా చెల్లింపును పూర్తి చేయండి.",
        "cta": "చెల్లింపును పూర్తి చేయండి",
    },
    (Language.TELUGU, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} payment poorti kaledu",
        "body": "Namaskaram {name}, mee Order #{order_id} kosam ₹{amount:,.2f} payment bank issue ({reason}) valla complete kaledu. Mee order reserve chesi unchamu.",
        "cta": "Malli Secure ga Pay Cheyandi",
    },

    # --- Kannada (Kannada Script) ---
    (Language.KANNADA, Script.KANNADA, Tone.EMPATHETIC): {
        "headline": "ಆರ್ಡರ್ #{order_id} ಪಾವತಿ ಪೂರ್ಣಗೊಂಡಿಲ್ಲ",
        "body": "ನಮಸ್ಕಾರ {name}, ನಿಮ್ಮ ಆರ್ಡರ್ #{order_id} ಗಾಗಿ ₹{amount:,.2f} ಪಾವತಿ ಬ್ಯಾಂಕ್ ಸಮಸ್ಯೆಯಿಂದಾಗಿ ({reason}) ವಿಫಲವಾಗಿದೆ. ನಿಮ್ಮ ಆರ್ಡರ್ ಸುರಕ್ಷಿತವಾಗಿದೆ.",
        "cta": "ಸುರಕ್ಷಿತವಾಗಿ ಮತ್ತೆ ಪಾವತಿಸಿ",
    },
    (Language.KANNADA, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} payment poornagondilla",
        "body": "Namaskara {name}, nimma Order #{order_id} ge ₹{amount:,.2f} payment bank issue ({reason}) inda aagilla. Order safe aagide.",
        "cta": "Mette Secure aagi Pay Maadi",
    },

    # --- Malayalam (Malayalam Script) ---
    (Language.MALAYALAM, Script.MALAYALAM, Tone.EMPATHETIC): {
        "headline": "ഓർഡർ #{order_id} പേയ്മെന്റ് പൂർത്തിയായില്ല",
        "body": "നമസ്കാരം {name}, നിങ്ങളുടെ ഓർഡർ #{order_id}-നായുള്ള ₹{amount:,.2f} പേയ്‌മെന്റ് ബാങ്ക് സാങ്കേതിക തകരാർ ({reason}) കാരണം പരാജയപ്പെട്ടു. നിങ്ങളുടെ ഓർഡർ സുരക്ഷിതമാണ്.",
        "cta": "സുരക്ഷിതമായി വീണ്ടും പണമടയ്ക്കുക",
    },
    (Language.MALAYALAM, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} payment poorthiyayilla",
        "body": "Namaskaram {name}, ningalude Order #{order_id} nu ulla ₹{amount:,.2f} payment bank issue ({reason}) kaaranam complete aayilla. Order safe aanu.",
        "cta": "Veendum Secure aayi Pay Cheyyuka",
    },

    # --- Marathi (Devanagari Script) ---
    (Language.MARATHI, Script.DEVANAGARI, Tone.EMPATHETIC): {
        "headline": "ऑर्डर #{order_id} चे पेमेंट अपूर्ण राहिले आहे",
        "body": "नमस्कार {name}, आपल्या ऑर्डर #{order_id} साठी ₹{amount:,.2f} चे पेमेंट बँकेच्या तांत्रिक समस्येमुळे ({reason}) अयशस्वी झाले. आपली ऑर्डर सुरक्षित आहे.",
        "cta": "पुन्हा सुरक्षित पेमेंट करा",
    },
    (Language.MARATHI, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} che payment apurna rahile",
        "body": "Namaskar {name}, aaplya Order #{order_id} sathi ₹{amount:,.2f} che payment bank technical issue ({reason}) mule fail zale. Order safe aahe.",
        "cta": "Punha Secure Payment Kara",
    },

    # --- Bengali (Bengali Script) ---
    (Language.BENGALI, Script.BENGALI, Tone.EMPATHETIC): {
        "headline": "অর্ডার #{order_id}-এর পেমেন্ট সম্পন্ন হয়নি",
        "body": "নমস্কার {name}, আপনার অর্ডার #{order_id}-এর জন্য ₹{amount:,.2f}-এর পেমেন্ট ব্যাঙ্কের সমস্যার ({reason}) কারণে সফল হয়নি। আপনার অর্ডারটি সুরক্ষিত আছে।",
        "cta": "পুনরায় নিরাপদ পেমেন্ট করুন",
    },
    (Language.BENGALI, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id}-er payment sompurno hoyni",
        "body": "Nomoshkar {name}, apnar Order #{order_id}-er jonno ₹{amount:,.2f} payment bank issue-r ({reason}) karone fail hoyeche. Order safe ache.",
        "cta": "Abar Secure Payment Korun",
    },

    # --- Gujarati (Gujarati Script) ---
    (Language.GUJARATI, Script.GUJARATI, Tone.EMPATHETIC): {
        "headline": "ઓર્ડર #{order_id} માટે ચૂકવણી સફળ થઈ નથી",
        "body": "નમસ્તે {name}, તમારા ઓર્ડર #{order_id} માટે ₹{amount:,.2f} ની ચૂકવણી બેંકની ટેકનિકલ સમસ્યા ({reason}) ને કારણે પૂર્ણ થઈ શકી નથી. તમારો ઓર્ડર સુરક્ષિત રાખવામાં આવ્યો છે.",
        "cta": "સુરક્ષિત રીતે ફરીથી ચૂકવો",
    },
    (Language.GUJARATI, Script.GUJARATI, Tone.PROFESSIONAL): {
        "headline": "ચૂકવણી સૂચના: ઓર્ડર #{order_id}",
        "body": "પ્રિય {name}, તમારા ઓર્ડર #{order_id} માટે ₹{amount:,.2f} ની લેવડદેવડ અસફળ રહી છે ({reason}). કૃપા કરીને નીચેની લિંક પરથી ચૂકવણી પૂર્ણ કરો.",
        "cta": "ચૂકવણી પૂર્ણ કરો",
    },
    (Language.GUJARATI, Script.LATIN, Tone.EMPATHETIC): {
        "headline": "Order #{order_id} mate payment safal thayu nathi",
        "body": "Namaste {name}, tamara Order #{order_id} mate ₹{amount:,.2f} nu payment bank issue ({reason}) na lidhe puru thayu nathi. Tamaro order safe chhe.",
        "cta": "Maro Pay Kari Ne Complete Karo",
    },
}


def get_template(language: Language, script: Script, tone: Tone) -> Dict[str, str]:
    if (language, script, tone) in TEMPLATES:
        return TEMPLATES[(language, script, tone)]
    if (language, script, Tone.EMPATHETIC) in TEMPLATES:
        return TEMPLATES[(language, script, Tone.EMPATHETIC)]
    if (language, Script.LATIN, tone) in TEMPLATES:
        return TEMPLATES[(language, Script.LATIN, tone)]
    return TEMPLATES.get(
        (Language.ENGLISH, Script.LATIN, tone),
        TEMPLATES[(Language.ENGLISH, Script.LATIN, Tone.EMPATHETIC)],
    )
