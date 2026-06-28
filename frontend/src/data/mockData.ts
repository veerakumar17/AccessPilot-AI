import type { DashboardStats, Project, Audit, Violation, Report } from '../types';

export const mockProjects: Project[] = [
  {
    id: 'proj-1',
    name: 'E-Commerce Platform',
    baseUrl: 'https://shop.example.com',
    description: 'Main e-commerce website with product listings, cart, and checkout flow.',
    createdAt: '2026-05-15T10:30:00Z',
    updatedAt: '2026-06-20T14:22:00Z',
  },
  {
    id: 'proj-2',
    name: 'Corporate Dashboard',
    baseUrl: 'https://dashboard.example.com',
    description: 'Internal analytics dashboard for business intelligence.',
    createdAt: '2026-04-10T08:00:00Z',
    updatedAt: '2026-06-18T09:15:00Z',
  },
  {
    id: 'proj-3',
    name: 'Healthcare Portal',
    baseUrl: 'https://health.example.com',
    description: 'Patient portal for appointment scheduling and medical records.',
    createdAt: '2026-03-22T12:45:00Z',
    updatedAt: '2026-06-19T16:30:00Z',
  },
  {
    id: 'proj-4',
    name: 'Learning Management System',
    baseUrl: 'https://learn.example.com',
    description: 'Online course platform with video lectures and assessments.',
    createdAt: '2026-02-05T09:00:00Z',
    updatedAt: '2026-06-15T11:00:00Z',
  },
  {
    id: 'proj-5',
    name: 'Banking App',
    baseUrl: 'https://bank.example.com',
    description: 'Digital banking application for account management and transactions.',
    createdAt: '2026-01-18T14:30:00Z',
    updatedAt: '2026-06-10T08:45:00Z',
  },
];

export const mockAudits: Audit[] = [
  {
    id: 'audit-001',
    projectId: 'proj-1',
    projectName: 'E-Commerce Platform',
    status: 'completed',
    score: 72,
    pagesScanned: 24,
    totalViolations: 47,
    criticalCount: 5,
    seriousCount: 12,
    moderateCount: 18,
    minorCount: 12,
    createdAt: '2026-06-20T10:00:00Z',
    completedAt: '2026-06-20T10:45:00Z',
  },
  {
    id: 'audit-002',
    projectId: 'proj-1',
    projectName: 'E-Commerce Platform',
    status: 'completed',
    score: 68,
    pagesScanned: 18,
    totalViolations: 53,
    criticalCount: 8,
    seriousCount: 15,
    moderateCount: 20,
    minorCount: 10,
    createdAt: '2026-06-15T09:00:00Z',
    completedAt: '2026-06-15T09:40:00Z',
  },
  {
    id: 'audit-003',
    projectId: 'proj-2',
    projectName: 'Corporate Dashboard',
    status: 'completed',
    score: 85,
    pagesScanned: 12,
    totalViolations: 22,
    criticalCount: 2,
    seriousCount: 5,
    moderateCount: 8,
    minorCount: 7,
    createdAt: '2026-06-18T08:30:00Z',
    completedAt: '2026-06-18T09:00:00Z',
  },
  {
    id: 'audit-004',
    projectId: 'proj-3',
    projectName: 'Healthcare Portal',
    status: 'in_progress',
    score: 0,
    pagesScanned: 8,
    totalViolations: 0,
    criticalCount: 0,
    seriousCount: 0,
    moderateCount: 0,
    minorCount: 0,
    createdAt: '2026-06-22T08:00:00Z',
    completedAt: null,
  },
  {
    id: 'audit-005',
    projectId: 'proj-4',
    projectName: 'Learning Management System',
    status: 'completed',
    score: 91,
    pagesScanned: 30,
    totalViolations: 15,
    criticalCount: 1,
    seriousCount: 3,
    moderateCount: 6,
    minorCount: 5,
    createdAt: '2026-06-12T11:00:00Z',
    completedAt: '2026-06-12T11:50:00Z',
  },
  {
    id: 'audit-006',
    projectId: 'proj-5',
    projectName: 'Banking App',
    status: 'failed',
    score: 0,
    pagesScanned: 5,
    totalViolations: 0,
    criticalCount: 0,
    seriousCount: 0,
    moderateCount: 0,
    minorCount: 0,
    createdAt: '2026-06-10T14:00:00Z',
    completedAt: null,
  },
  {
    id: 'audit-007',
    projectId: 'proj-2',
    projectName: 'Corporate Dashboard',
    status: 'completed',
    score: 78,
    pagesScanned: 15,
    totalViolations: 35,
    criticalCount: 4,
    seriousCount: 9,
    moderateCount: 14,
    minorCount: 8,
    createdAt: '2026-06-05T10:00:00Z',
    completedAt: '2026-06-05T10:35:00Z',
  },
  {
    id: 'audit-008',
    projectId: 'proj-1',
    projectName: 'E-Commerce Platform',
    status: 'pending',
    score: 0,
    pagesScanned: 0,
    totalViolations: 0,
    criticalCount: 0,
    seriousCount: 0,
    moderateCount: 0,
    minorCount: 0,
    createdAt: '2026-06-22T06:00:00Z',
    completedAt: null,
  },
];

export const mockViolations: Violation[] = [
  // Violations for audit-001 (E-Commerce Platform) - 6 violations
  {
    id: 'viol-001',
    auditId: 'audit-001',
    ruleId: 'WCAG-2.4.4',
    severity: 'critical',
    description: 'Links must have discernible text',
    htmlSnippet: '<a href="/product/123" class="card-link"><img src="product.jpg" alt=""></a>',
    wcagCriterion: '2.4.4 Link Purpose (In Context)',
    impact: 'Screen reader users cannot navigate or understand the purpose of links without text.',
    aiExplanation: {
      plainEnglish: 'This link contains only an image with an empty alt attribute. Screen readers will skip over it entirely, making the link invisible to blind users.',
      businessImpact: 'Approximately 8% of your users with visual impairments cannot access product links, potentially losing $120K in annual revenue from this demographic.',
      recommendation: 'Add descriptive alt text to the image or wrap the link around text that describes the destination.',
    },
    aiFix: {
      problem: 'The anchor tag wraps an image with alt="" which provides no text for screen readers to announce as a link.',
      recommendedFix: 'Add meaningful alt text to the image that describes the link destination, or add visible text within the link.',
      codeExample: '<a href="/product/123" class="card-link">\n  <img src="product.jpg" alt="View Product 123 - Wireless Headphones">\n  <span class="sr-only">View Product 123</span>\n</a>',
      implementationSteps: [
        'Identify the product name from the image context or data attribute',
        'Add descriptive alt text to the img element',
        'Optionally add a visually hidden span with link text',
        'Test with a screen reader to verify the link is announced correctly',
      ],
      priority: 'high',
    },
    disabilitySimulation: {
      blind: {
        severity: 'severe',
        explanation: 'Blind users rely entirely on screen readers to navigate. This link is completely invisible to them.',
        userExperience: 'A blind user tabbing through the page will hear nothing at this point. They will miss this product link entirely and may not be able to complete a purchase.',
      },
      lowVision: {
        severity: 'moderate',
        explanation: 'Users with low vision who use screen magnifiers may see the image but cannot interact with it as a link.',
        userExperience: 'A user with low vision zoomed in may see the product image but have no indication it is clickable, missing navigation cues.',
      },
      motor: {
        severity: 'mild',
        explanation: 'Motor disabilities are not directly impacted by missing link text, but tabbing through invisible links wastes effort.',
        userExperience: 'A user navigating by keyboard will tab to an empty link, wasting time and causing confusion about what was focused.',
      },
      cognitive: {
        severity: 'mild',
        explanation: 'Users with cognitive disabilities benefit from clear, descriptive link text that sets expectations.',
        userExperience: 'A user with cognitive disabilities may click the image without understanding where it leads, causing confusion.',
      },
    },
  },
  {
    id: 'viol-002',
    auditId: 'audit-001',
    ruleId: 'WCAG-1.1.1',
    severity: 'critical',
    description: 'Images must have alt text',
    htmlSnippet: '<img src="/banners/sale-banner.jpg" class="hero-banner" />',
    wcagCriterion: '1.1.1 Non-text Content',
    impact: 'Screen readers cannot convey the content or purpose of images without alternative text.',
    aiExplanation: {
      plainEnglish: 'This decorative or informative image has no alt attribute at all. Screen readers will read the filename instead, which is meaningless.',
      businessImpact: 'Users relying on screen readers miss promotional content, reducing engagement by up to 15% for visually impaired users.',
      recommendation: 'Add an alt attribute with descriptive text for informative images, or alt="" for purely decorative images.',
    },
    aiFix: {
      problem: 'The img element is missing the alt attribute entirely, causing screen readers to announce the file path.',
      recommendedFix: 'Add an appropriate alt attribute based on the image purpose.',
      codeExample: '<!-- Informative image -->\n<img src="/banners/sale-banner.jpg" class="hero-banner" alt="Summer Sale - 40% off all items until July 31st" />\n\n<!-- Decorative image -->\n<img src="/banners/sale-banner.jpg" class="hero-banner" alt="" role="presentation" />',
      implementationSteps: [
        'Determine if the image is informative or decorative',
        'For informative images: write concise alt text describing the content',
        'For decorative images: set alt="" and add role="presentation"',
        'Verify with a screen reader that the image is handled correctly',
      ],
      priority: 'high',
    },
    disabilitySimulation: {
      blind: {
        severity: 'severe',
        explanation: 'Blind users cannot perceive visual content. Without alt text, the image information is lost entirely.',
        userExperience: 'A blind user hears "bannerslashsale-banner.jpg" announced, which is confusing and unhelpful. They miss the sale promotion entirely.',
      },
      lowVision: {
        severity: 'moderate',
        explanation: 'Users with low vision may partially see the image but need text alternatives for full understanding.',
        userExperience: 'A user with low vision sees a blurry banner but cannot read the text. Without alt text, they cannot access the sale information.',
      },
      motor: {
        severity: 'none',
        explanation: 'This issue does not directly impact users with motor disabilities.',
        userExperience: 'No significant impact on motor-impaired users.',
      },
      cognitive: {
        severity: 'mild',
        explanation: 'Users with cognitive disabilities benefit from text alternatives that reinforce visual content.',
        userExperience: 'A user with cognitive disabilities may see the banner but not process the visual information. Alt text provides reinforcement.',
      },
    },
  },
  {
    id: 'viol-003',
    auditId: 'audit-001',
    ruleId: 'WCAG-1.4.3',
    severity: 'serious',
    description: 'Color contrast ratio is insufficient',
    htmlSnippet: '<button class="btn-subtle" style="color: #888888; background: #f0f0f0;">Continue</button>',
    wcagCriterion: '1.4.3 Contrast (Minimum)',
    impact: 'Users with low vision cannot read text that does not have sufficient contrast against its background.',
    aiExplanation: {
      plainEnglish: 'The gray text (#888) on light gray background (#f0f0f0) has a contrast ratio of approximately 2.5:1, well below the required 4.5:1 for normal text.',
      businessImpact: 'Up to 5% of users with color vision deficiencies will struggle to read this button text, potentially causing form abandonment.',
      recommendation: 'Darken the text color or lighten the background to achieve at least 4.5:1 contrast ratio for normal text.',
    },
    aiFix: {
      problem: 'The contrast ratio between #888888 text and #f0f0f0 background is only 2.5:1, failing WCAG AA requirements.',
      recommendedFix: 'Use a darker text color such as #333333 or #444444 to achieve sufficient contrast.',
      codeExample: '<button class="btn-subtle" style="color: #333333; background: #f0f0f0;">Continue</button>\n/* Or use CSS */\n.btn-subtle {\n  color: #333333;\n  background-color: #f0f0f0;\n  /* Contrast ratio: 9.8:1 - passes WCAG AAA */\n}',
      implementationSteps: [
        'Measure current contrast ratio using a tool like WebAIM Contrast Checker',
        'Select a darker text color that achieves at least 4.5:1 ratio',
        'Update the CSS or inline styles',
        'Verify the fix with a contrast checking tool',
      ],
      priority: 'high',
    },
    disabilitySimulation: {
      blind: {
        severity: 'none',
        explanation: 'Color contrast does not affect blind users who use screen readers.',
        userExperience: 'No direct impact on blind users.',
      },
      lowVision: {
        severity: 'severe',
        explanation: 'Users with low vision or color blindness cannot distinguish low-contrast text from its background.',
        userExperience: 'A user with low vision sees a blank button or must strain significantly to read "Continue". Many will give up and leave the page.',
      },
      motor: {
        severity: 'none',
        explanation: 'This issue does not directly impact users with motor disabilities.',
        userExperience: 'No significant impact on motor-impaired users.',
      },
      cognitive: {
        severity: 'moderate',
        explanation: 'Low contrast text requires more cognitive effort to read, increasing cognitive load.',
        userExperience: 'A user with cognitive disabilities must expend extra mental energy deciphering the text, leading to faster fatigue.',
      },
    },
  },
  {
    id: 'viol-004',
    auditId: 'audit-001',
    ruleId: 'WCAG-2.1.1',
    severity: 'serious',
    description: 'Keyboard trap in search modal',
    htmlSnippet: '<div class="search-modal" role="dialog">\n  <input type="text" placeholder="Search products...">\n  <button onclick="closeModal()">Close</button>\n</div>',
    wcagCriterion: '2.1.1 Keyboard',
    impact: 'Users who cannot use a mouse cannot navigate out of the search modal using keyboard alone.',
    aiExplanation: {
      plainEnglish: 'When the search modal opens, keyboard focus is trapped inside. Users cannot Tab out or press Escape to close it, making the modal inescapable without a mouse.',
      businessImpact: 'Keyboard-only users (including many power users and users with motor disabilities) cannot use the search feature, affecting approximately 10% of your user base.',
      recommendation: 'Add keyboard event handling for Escape key and ensure focus can move out of the modal naturally.',
    },
    aiFix: {
      problem: 'The modal lacks keyboard event listeners for Escape and does not manage focus properly, creating a keyboard trap.',
      recommendedFix: 'Add keyboard event handling and focus management to the modal component.',
      codeExample: 'useEffect(() => {\n  const handleKeyDown = (e: KeyboardEvent) => {\n    if (e.key === "Escape") {\n      closeModal();\n    }\n  };\n  document.addEventListener("keydown", handleKeyDown);\n  // Trap focus within modal\n  const focusableEls = modalRef.current.querySelectorAll(\n    "button, input, [tabindex]:not([tabindex=\\"-1\\"])"\n  );\n  if (focusableEls.length > 0) {\n    (focusableEls[0] as HTMLElement).focus();\n  }\n  return () => document.removeEventListener("keydown", handleKeyDown);\n}, []);',
      implementationSteps: [
        'Add an onKeyDown handler to the modal container',
        'Handle Escape key to close the modal',
        'Implement focus trapping: keep focus within modal while open',
        'Return focus to the element that triggered the modal on close',
        'Test navigation with Tab key only',
      ],
      priority: 'high',
    },
    disabilitySimulation: {
      blind: {
        severity: 'severe',
        explanation: 'Blind users navigating by keyboard cannot escape the modal, effectively locking them out of the rest of the page.',
        userExperience: 'A blind user opens the search modal and cannot leave. They are trapped and may need to refresh the page, losing any unsaved work.',
      },
      lowVision: {
        severity: 'moderate',
        explanation: 'Users with low vision using keyboard navigation face the same trap, though they may visually see the close button.',
        userExperience: 'A user with low vision tabs through the modal repeatedly, unable to reach the close button or return to the main page.',
      },
      motor: {
        severity: 'severe',
        explanation: 'Users with motor disabilities who rely on keyboard or switch devices cannot escape the modal trap.',
        userExperience: 'A user with limited hand mobility using a keyboard cannot Tab out. They may need assistance or must force-quit the browser.',
      },
      cognitive: {
        severity: 'moderate',
        explanation: 'Being trapped in a modal can cause anxiety and confusion for users with cognitive disabilities.',
        userExperience: 'A user with cognitive disabilities becomes frustrated and confused when they cannot leave the search box, potentially causing an emotional response.',
      },
    },
  },
  {
    id: 'viol-005',
    auditId: 'audit-001',
    ruleId: 'WCAG-4.1.2',
    severity: 'moderate',
    description: 'Form inputs missing associated labels',
    htmlSnippet: '<div class="form-group">\n  <input type="email" placeholder="Enter your email" class="form-input">\n</div>',
    wcagCriterion: '4.1.2 Name, Role, Value',
    impact: 'Screen readers cannot identify the purpose of form inputs without programmatically associated labels.',
    aiExplanation: {
      plainEnglish: 'This email input uses a placeholder instead of a proper label. Placeholders disappear when typing and are not reliably announced by all screen readers.',
      businessImpact: 'Users with screen readers may not know what information to enter, causing form errors and abandonment rates up to 20% higher.',
      recommendation: 'Add a proper <label> element associated with the input via the "for" attribute or by wrapping the input.',
    },
    aiFix: {
      problem: 'The input field relies on a placeholder for its label, which is not a valid accessible labeling technique.',
      recommendedFix: 'Add a visible label element associated with the input using the htmlFor attribute.',
      codeExample: '<div class="form-group">\n  <label htmlFor="email" class="form-label">Email Address</label>\n  <input \n    type="email" \n    id="email" \n    placeholder="Enter your email" \n    className="form-input"\n  />\n</div>',
      implementationSteps: [
        'Add a label element before or around the input',
        'Set the label htmlFor attribute to match the input id',
        'Ensure the label contains visible text describing the input purpose',
        'Remove placeholder-only dependency (keep placeholder as supplementary)',
        'Test with a screen reader to verify the label is announced',
      ],
      priority: 'medium',
    },
    disabilitySimulation: {
      blind: {
        severity: 'severe',
        explanation: 'Blind users rely on labels to know what to enter in each field. Without labels, forms are unusable.',
        userExperience: 'A blind user tabs to this field and hears "edit text" with no context. They do not know whether to enter their name, email, or phone number.',
      },
      lowVision: {
        severity: 'moderate',
        explanation: 'Users with low vision may see the placeholder but it disappears on input, causing confusion.',
        userExperience: 'A user with low vision zooms in, sees "Enter your email", starts typing, and the text disappears. They may forget what field they are filling.',
      },
      motor: {
        severity: 'mild',
        explanation: 'Motor-impaired users benefit from larger click targets that labels provide.',
        userExperience: 'A user with limited fine motor control can click the label to focus the input, but without a label they must target the small input field precisely.',
      },
      cognitive: {
        severity: 'moderate',
        explanation: 'Users with cognitive disabilities need persistent labels to understand form fields.',
        userExperience: 'A user with memory issues reads the placeholder, then looks away to find their email. When they return, the placeholder is gone and they cannot remember what to type.',
      },
    },
  },
  {
    id: 'viol-006',
    auditId: 'audit-001',
    ruleId: 'WCAG-2.4.7',
    severity: 'moderate',
    description: 'Focus indicator is missing or insufficient',
    htmlSnippet: '<a href="/checkout" class="checkout-btn" style="outline: none;">Proceed to Checkout</a>',
    wcagCriterion: '2.4.7 Focus Visible',
    impact: 'Keyboard users cannot determine which element has focus, making navigation confusing and error-prone.',
    aiExplanation: {
      plainEnglish: 'The checkout button has outline: none, removing the default focus indicator. Keyboard users cannot see where their focus is on the page.',
      businessImpact: 'Keyboard users may accidentally click the wrong button or submit incomplete forms, increasing support tickets by up to 12%.',
      recommendation: 'Remove outline: none or provide a custom focus style that is highly visible.',
    },
    aiFix: {
      problem: 'The CSS rule outline: none removes the visible focus ring, making keyboard navigation invisible.',
      recommendedFix: 'Replace with a custom focus style that is visible against the background.',
      codeExample: '.checkout-btn:focus-visible {\n  outline: 2px solid #2563eb;\n  outline-offset: 2px;\n  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.3);\n}\n\n/* Remove only for mouse users */\n.checkout-btn:focus:not(:focus-visible) {\n  outline: none;\n}',
      implementationSteps: [
        'Remove the outline: none rule or replace it',
        'Add a :focus-visible style with a prominent outline or ring',
        'Use a color that contrasts well with the button background',
        'Ensure the focus indicator is at least 2px thick',
        'Test by tabbing through all interactive elements',
      ],
      priority: 'medium',
    },
    disabilitySimulation: {
      blind: {
        severity: 'none',
        explanation: 'Visual focus indicators do not affect blind screen reader users.',
        userExperience: 'No direct impact on blind users.',
      },
      lowVision: {
        severity: 'severe',
        explanation: 'Users with low vision who use screen magnification need clear focus indicators to track their position.',
        userExperience: 'A user with low vision tabs through the page but cannot see where the focus is. They may click the wrong link or become disoriented.',
      },
      motor: {
        severity: 'severe',
        explanation: 'Keyboard-dependent users need visible focus to navigate efficiently.',
        userExperience: 'A user with motor disabilities who navigates by keyboard tabs through the page blindly, unable to tell which button will be activated on Enter.',
      },
      cognitive: {
        severity: 'moderate',
        explanation: 'Users with cognitive disabilities rely on visual cues to track their navigation progress.',
        userExperience: 'A user with attention deficits loses track of their position on the page, becoming confused about which element they are about to interact with.',
      },
    },
  },
  // Violations for audit-003 (Corporate Dashboard) - 2 violations
  {
    id: 'viol-007',
    auditId: 'audit-003',
    ruleId: 'WCAG-2.4.4',
    severity: 'critical',
    description: 'Dashboard navigation links missing discernible text',
    htmlSnippet: '<nav><a href="/reports" class="nav-icon"><svg><!-- icon --></svg></a></nav>',
    wcagCriterion: '2.4.4 Link Purpose (In Context)',
    impact: 'Screen reader users cannot navigate the dashboard sidebar.',
    aiExplanation: {
      plainEnglish: 'The dashboard navigation uses icons-only links without any text or aria-label, making them inaccessible to screen readers.',
      businessImpact: 'Keyboard and screen reader users cannot navigate the dashboard, affecting productivity of employees with disabilities.',
      recommendation: 'Add visually hidden text or aria-label attributes to all icon-only navigation links.',
    },
    aiFix: {
      problem: 'Navigation links contain only SVG icons with no accessible text.',
      recommendedFix: 'Add aria-label attributes to each navigation link describing its destination.',
      codeExample: '<nav>\n  <a href="/reports" class="nav-icon" aria-label="Reports">\n    <svg><!-- icon --></svg>\n  </a>\n</nav>',
      implementationSteps: [
        'Identify all icon-only navigation links',
        'Add aria-label attributes with descriptive text',
        'Ensure each label uniquely identifies the link destination',
        'Test with screen reader to verify announcements',
      ],
      priority: 'high',
    },
    disabilitySimulation: {
      blind: {
        severity: 'severe',
        explanation: 'Without text alternatives, blind users cannot identify navigation options.',
        userExperience: 'A blind user tabs through the sidebar hearing only "link, link, link" with no context about where each link goes.',
      },
      lowVision: { severity: 'mild', explanation: 'Users with some vision may see the icons and infer meaning.', userExperience: 'A user with low vision may partially recognize icons but still struggle with unfamiliar ones.' },
      motor: { severity: 'none', explanation: 'Not directly impacted.', userExperience: 'No significant impact.' },
      cognitive: { severity: 'moderate', explanation: 'Icon-only navigation requires higher cognitive load.', userExperience: 'A user with cognitive disabilities may not understand icon meanings, leading to confusion.' },
    },
  },
  {
    id: 'viol-008',
    auditId: 'audit-003',
    ruleId: 'WCAG-1.4.3',
    severity: 'serious',
    description: 'Chart text insufficient contrast ratio',
    htmlSnippet: '<text fill="#9CA3AF" font-size="12">Q1 Revenue: $1.2M</text>',
    wcagCriterion: '1.4.3 Contrast (Minimum)',
    impact: 'Users with low vision cannot read chart labels and data points.',
    aiExplanation: {
      plainEnglish: 'The chart uses gray text (#9CA3AF) on the dashboard background (#0F172A), resulting in a contrast ratio of approximately 3.2:1, below the 4.5:1 standard.',
      businessImpact: 'Data-driven decisions rely on readable charts. Low contrast reduces comprehension for all users in bright environments.',
      recommendation: 'Use a lighter shade for chart text, such as #E5E7EB or increase font weight.',
    },
    aiFix: {
      problem: 'Chart text color does not meet minimum contrast requirements.',
      recommendedFix: 'Change text color to #E5E7EB or higher contrast alternative.',
      codeExample: '<text fill="#E5E7EB" font-size="12" font-weight="500">Q1 Revenue: $1.2M</text>',
      implementationSteps: ['Identify low-contrast text elements', 'Update fill color to meet 4.5:1 ratio', 'Verify with contrast checker tool'],
      priority: 'medium',
    },
    disabilitySimulation: {
      blind: { severity: 'none', explanation: 'Not applicable.', userExperience: 'No impact.' },
      lowVision: { severity: 'severe', explanation: 'Gray text on dark background is extremely hard to read.', userExperience: 'A user with low vision cannot read the chart values, missing key data insights.' },
      motor: { severity: 'none', explanation: 'Not directly impacted.', userExperience: 'No significant impact.' },
      cognitive: { severity: 'mild', explanation: 'Harder to read text increases cognitive load.', userExperience: 'A user must strain to read, causing faster fatigue.' },
    },
  },
  // Violations for audit-005 (Learning Management System) - 2 violations
  {
    id: 'viol-009',
    auditId: 'audit-005',
    ruleId: 'WCAG-2.4.7',
    severity: 'moderate',
    description: 'Course navigation focus indicator missing',
    htmlSnippet: '<div class="course-nav" tabindex="0" style="outline: none;">Week 1: Introduction</div>',
    wcagCriterion: '2.4.7 Focus Visible',
    impact: 'Keyboard users cannot track their position in the course navigation.',
    aiExplanation: {
      plainEnglish: 'The course week navigation removes the focus outline, making it impossible for keyboard users to see which week is currently focused.',
      businessImpact: 'Students who navigate by keyboard may select the wrong week, causing frustration and support requests.',
      recommendation: 'Add a visible focus indicator using focus-visible CSS pseudo-class.',
    },
    aiFix: {
      problem: 'outline: none removes the visible focus ring from interactive course navigation elements.',
      recommendedFix: 'Add a custom focus style using focus-visible.',
      codeExample: '.course-nav:focus-visible {\n  outline: 2px solid #3B82F6;\n  outline-offset: 2px;\n  border-radius: 4px;\n}',
      implementationSteps: ['Remove outline: none', 'Add :focus-visible styles', 'Test keyboard navigation'],
      priority: 'medium',
    },
    disabilitySimulation: {
      blind: { severity: 'none', explanation: 'Not applicable.', userExperience: 'No direct impact.' },
      lowVision: { severity: 'severe', explanation: 'No focus indicator makes keyboard navigation impossible.', userExperience: 'A user with low vision tabs through weeks but cannot see which is selected.' },
      motor: { severity: 'severe', explanation: 'Keyboard users need visible focus to navigate.', userExperience: 'A motor-impaired user navigating by keyboard cannot tell which course week will be opened.' },
      cognitive: { severity: 'moderate', explanation: 'Lost focus causes confusion.', userExperience: 'A user with attention deficits loses track of position in the course content.' },
    },
  },
  {
    id: 'viol-010',
    auditId: 'audit-005',
    ruleId: 'WCAG-4.1.2',
    severity: 'minor',
    description: 'Video player controls missing ARIA labels',
    htmlSnippet: '<button class="vjs-play-control vjs-control" type="button"><span class="vjs-icon-placeholder"></span></button>',
    wcagCriterion: '4.1.2 Name, Role, Value',
    impact: 'Screen reader users cannot identify video player controls.',
    aiExplanation: {
      plainEnglish: 'The video play button uses an icon-only approach without an aria-label. Screen readers announce it as "button" with no function context.',
      businessImpact: 'Students with visual impairments cannot control video playback, limiting access to course content.',
      recommendation: 'Add aria-label="Play" or "Pause" to the video control buttons.',
    },
    aiFix: {
      problem: 'Video player control buttons lack accessible labels.',
      recommendedFix: 'Add aria-label attributes to all video player controls.',
      codeExample: '<button class="vjs-play-control vjs-control" type="button" aria-label="Play video">\n  <span class="vjs-icon-placeholder"></span>\n</button>',
      implementationSteps: ['Identify all video controls', 'Add descriptive aria-labels', 'Test with screen reader'],
      priority: 'low',
    },
    disabilitySimulation: {
      blind: { severity: 'severe', explanation: 'Cannot identify or use video controls.', userExperience: 'A blind user hears "button" with no context and cannot play the lecture video.' },
      lowVision: { severity: 'mild', explanation: 'May see the icon.', userExperience: 'Partial visibility but no text confirmation.' },
      motor: { severity: 'none', explanation: 'Not directly impacted.', userExperience: 'No significant impact.' },
      cognitive: { severity: 'mild', explanation: 'ARIA labels help reinforce visual cues.', userExperience: 'Text labels help confirm button function.' },
    },
  },
];

export const mockReports: Report[] = [
  {
    id: 'rpt-001',
    auditId: 'audit-001',
    projectName: 'E-Commerce Platform',
    score: 72,
    grade: 'C',
    totalViolations: 47,
    criticalCount: 5,
    seriousCount: 12,
    moderateCount: 18,
    minorCount: 12,
    summary: 'The E-Commerce Platform has significant accessibility issues that need immediate attention. Critical violations include missing link text and missing image alt attributes. The site fails WCAG 2.1 AA compliance and requires remediation of 47 total violations across 24 scanned pages.',
    generatedAt: '2026-06-20T11:00:00Z',
  },
  {
    id: 'rpt-002',
    auditId: 'audit-003',
    projectName: 'Corporate Dashboard',
    score: 85,
    grade: 'B',
    totalViolations: 22,
    criticalCount: 2,
    seriousCount: 5,
    moderateCount: 8,
    minorCount: 7,
    summary: 'The Corporate Dashboard performs reasonably well with an 85 score. Two critical issues need addressing: keyboard traps in modal dialogs and missing form labels. Overall, the application is partially compliant with WCAG 2.1 AA standards.',
    generatedAt: '2026-06-18T09:15:00Z',
  },
  {
    id: 'rpt-003',
    auditId: 'audit-005',
    projectName: 'Learning Management System',
    score: 91,
    grade: 'A',
    totalViolations: 15,
    criticalCount: 1,
    seriousCount: 3,
    moderateCount: 6,
    minorCount: 5,
    summary: 'The Learning Management System demonstrates strong accessibility practices with a 91 score. Only 15 minor to moderate violations were found. The single critical issue involves a focus indicator on the course navigation menu. The platform is close to full WCAG 2.1 AA compliance.',
    generatedAt: '2026-06-12T12:00:00Z',
  },
];

export const mockDashboardStats: DashboardStats = {
  totalProjects: 5,
  totalAudits: 8,
  accessibilityScore: 72,
  criticalViolations: 5,
  recentAudits: mockAudits.slice(0, 4),
};

export const getGrade = (score: number): string => {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
};

export const getGradeColor = (grade: string): string => {
  switch (grade) {
    case 'A': return 'text-green-400';
    case 'B': return 'text-blue-400';
    case 'C': return 'text-yellow-400';
    case 'D': return 'text-orange-400';
    case 'F': return 'text-red-400';
    default: return 'text-gray-400';
  }
};

export const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'serious': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'moderate': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'minor': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed': return 'bg-green-500/20 text-green-400';
    case 'in_progress': return 'bg-blue-500/20 text-blue-400';
    case 'failed': return 'bg-red-500/20 text-red-400';
    case 'pending': return 'bg-gray-500/20 text-gray-400';
    default: return 'bg-gray-500/20 text-gray-400';
  }
};

export const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'high': return 'text-red-400';
    case 'medium': return 'text-yellow-400';
    case 'low': return 'text-green-400';
    default: return 'text-gray-400';
  }
};