/**
 * Frontend Prompt boundary.
 *
 * The backend owns final visual Prompt compilation and returns a clean
 * copyable string.  This module only provides a small display fallback for
 * unsaved drafts and the independent MiniMax audio preparation helpers.  It
 * never appends workflow metadata or the old visual Prompt fields.
 */

export const PROMPT_CONTRACT_VERSION = '3.0-style-library';
export const PROMPT_WORKFLOW_ID = 'style-library-visual-v1';
export const AUDIO_PROMPT_SCHEMA_VERSION = 'minimax-speech-audio-v2';
export const AUDIO_PROMPT_FIELD_ORDER = [
  'sourceText', 'providerText', 'textStatus', 'voiceSource', 'voiceIdentity', 'language', 'locale', 'dialect',
  'providerVoiceId', 'providerVoiceName', 'providerRegion', 'performanceDirection', 'emotion', 'intensity',
  'pace', 'pausePlan', 'pronunciation', 'provider', 'model', 'voiceId', 'speed', 'pitch', 'volume',
  'languageBoost', 'format', 'targetDuration', 'relevantShots', 'continuityChecklist', 'mustPreserve', 'mustAvoid',
] as const;

export type PromptCompositionMode = 'style_library';
export type PromptRecord = Record<string, unknown>;
export type PromptContext = {
  shots?: PromptRecord[];
  references?: unknown[];
  assetGenerationProfile?: Record<string, unknown>;
  assetLayoutProfile?: string | null;
  outputAspectRatio?: string;
};

const classAliases: Record<string, string> = {
  environment: 'scene', environment_prop: 'scene', environment_state: 'scene', background: 'scene', landscape: 'scene',
  item: 'prop', vfx: 'prop', weapon_effect: 'prop', mechanical_effect: 'prop',
  dialogue: 'audio', voice: 'audio', mix: 'audio',
};
const baseAssetClasses = new Set(['character', 'scene', 'prop', 'product']);
const baseAssetAspectRatios: Record<string, string> = { character: '16:9', scene: '16:9', prop: '1:1', product: '1:1', style: '16:9' };
const styleLabels: Record<string, string> = {
  '3D': '3D', Architecture: '建筑空间', Brand: '品牌视觉', Character: '角色设计', Characters: '人物表现',
  Charts: '图表信息可视化', Classical: '古典气质', Documents: '出版物版式', History: '历史题材',
  Illustration: '插画', Infographic: '信息图', 'Other Use Cases': '特殊研发视觉', Photography: '摄影',
  Poster: '海报排版', Product: '产品视觉', Products: '商品视觉', Realistic: '写实', Scenes: '场景叙事', UI: '界面视觉',
};
const legacyMarkers = [
  'suyu-skill-v2', 'base-asset-v1', 'legacy_supplement', '同时满足以下补充制作要求', 'Prompt Contract', 'FRAMEFLOW',
  'Image Execution Prompt', '资产 ID', 'Prompt QA', 'generationStatus', 'imageGenerationEligible', 'providerAspectRatio',
  'provider_aspect_ratio', '1536x1024', '1024x1024', '1024x1536', 'openai', 'OpenAI', 'opencode', 'OpenCode',
  'promptPack', 'promptQuality', 'user-confirmation-required', 'generationNotes', 'suggestedSize', 'identityAnchor',
  'visibleEvent', 'characterDetails', 'sceneDetails', 'propDetails', 'fusionDetails', 'shotPlan', 'mustPreserve',
  'mustAvoid', 'negativePrompt', 'visualStyle', 'cameraExecution', 'lightingCausality', 'atmosphereBehavior',
];
const legacyVisualPackFields = new Set([
  'promptIntent', 'referenceStrategy', 'generationReferenceAssets', 'identityAnchor', 'identityLock',
  'visibleEvent', 'spatialGeography', 'materialEvidence', 'lightingCausality', 'cameraExecution',
  'atmosphereBehavior', 'characterDetails', 'sceneDetails', 'propDetails', 'itemDetails', 'fusionDetails',
  'shotPlan', 'visualStyle', 'continuityChecklist', 'negativePrompt', 'generationNotes', 'suggestedSize',
  'detailAnchorRegistry', 'mustPreserve', 'mustAvoid', 'assetGenerationSize', 'assetProviderAspectRatio',
  'imageExecutionPrompt', 'imageGenerationEligible', 'promptFieldOrder', 'prompt_field_order',
]);
const newVisualPackFields = ['subjectTask', 'compositionLayout', 'visualStyleMaterials', 'textLabels', 'aspectRatioOutput', 'constraintsNegative'];
const pixelSizePattern = /(?<![A-Za-z0-9])\d{3,5}\s*[x×]\s*\d{3,5}(?![A-Za-z0-9])/i;
const internalIdPattern = /(?<![A-Za-z0-9])(?:ASSET|ARTIFACT|PROMPT|RUN|CHAR|SH|SCENE|PROP|ITEM|C|S|P|FUSION)[_-]?\d{1,5}[A-Z]?(?![A-Za-z0-9])/gi;

export type MiniMaxWebPromptPackage = {
  schemaVersion: string;
  provider: 'minimax';
  operation: string;
  sourceText: string;
  providerText: string;
  copyText: string;
  candidateText: string;
  textStatus: string;
  direction: string;
  settings: Record<string, string>;
  pausePlan: unknown;
  pronunciation: unknown;
  soundTags: unknown;
  targetDuration: unknown;
  relevantShots: unknown;
  candidates: Array<{ shotId: string; kind: string; text: string }>;
  continuity: string[];
  mustPreserve: string[];
  mustAvoid: string[];
  warnings: string[];
};

const audioLocaleLanguageBoosts: Record<string, string> = {
  ja: 'Japanese', 'ja-jp': 'Japanese', zh: 'Chinese', 'zh-cn': 'Chinese', 'zh-tw': 'Chinese',
  en: 'English', 'en-us': 'English', 'en-gb': 'English', ko: 'Korean', 'ko-kr': 'Korean',
  fr: 'French', 'fr-fr': 'French', de: 'German', 'de-de': 'German', es: 'Spanish', 'es-es': 'Spanish',
  it: 'Italian', 'it-it': 'Italian', pt: 'Portuguese', 'pt-br': 'Portuguese', 'pt-pt': 'Portuguese',
  ru: 'Russian', 'ru-ru': 'Russian', ar: 'Arabic', tr: 'Turkish', nl: 'Dutch', vi: 'Vietnamese',
  id: 'Indonesian', 'id-id': 'Indonesian', th: 'Thai', 'th-th': 'Thai', ms: 'Malay', 'ms-my': 'Malay',
  fil: 'Filipino', 'fil-ph': 'Filipino', uk: 'Ukrainian', 'uk-ua': 'Ukrainian', pl: 'Polish', 'pl-pl': 'Polish',
  ro: 'Romanian', 'ro-ro': 'Romanian', cs: 'Czech', 'cs-cz': 'Czech', el: 'Greek', 'el-gr': 'Greek',
  hu: 'Hungarian', 'hu-hu': 'Hungarian', sv: 'Swedish', 'sv-se': 'Swedish', da: 'Danish', 'da-dk': 'Danish',
  fi: 'Finnish', 'fi-fi': 'Finnish', no: 'Norwegian', 'no-no': 'Norwegian', sk: 'Slovak', 'sk-sk': 'Slovak',
  bg: 'Bulgarian', 'bg-bg': 'Bulgarian', hr: 'Croatian', 'hr-hr': 'Croatian', ta: 'Tamil', 'ta-in': 'Tamil',
  te: 'Telugu', 'te-in': 'Telugu', hi: 'Hindi', 'hi-in': 'Hindi', he: 'Hebrew', 'he-il': 'Hebrew',
  fa: 'Persian', 'fa-ir': 'Persian', bn: 'Bengali', 'bn-bd': 'Bengali', af: 'Afrikaans', 'af-za': 'Afrikaans',
  ca: 'Catalan', 'ca-es': 'Catalan', sr: 'Serbian', 'sr-rs': 'Serbian',
};
const audioConfirmedTextStatuses = new Set(['confirmed', 'user-confirmed', 'approved', 'locked', 'final']);

export function canonicalAssetClass(assetClass?: string): string {
  const value = String(assetClass || 'unknown').trim().toLowerCase();
  return classAliases[value] || value;
}

export function isBaseAssetClass(assetClass?: string): boolean {
  return baseAssetClasses.has(canonicalAssetClass(assetClass));
}

export function promptCompositionModeForAsset(_assetClass?: string, _requested: PromptCompositionMode = 'style_library'): PromptCompositionMode {
  return 'style_library';
}

function isRecord(value: unknown): value is PromptRecord {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined || value === false) return false;
  if (typeof value === 'string') return Boolean(value.trim());
  if (Array.isArray(value)) return value.some(hasValue);
  if (isRecord(value)) return Object.values(value).some(hasValue);
  return true;
}

function text(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value).trim();
  if (Array.isArray(value)) return value.map(text).filter(Boolean).join('；');
  if (isRecord(value)) return Object.values(value).map(text).filter(Boolean).join('；');
  return String(value).trim();
}

function first(source: PromptRecord, keys: string[]): unknown {
  for (const key of keys) if (hasValue(source[key])) return source[key];
  return undefined;
}

function list(value: unknown): string[] {
  const values = Array.isArray(value) ? value : hasValue(value) ? [value] : [];
  return [...new Set(values.map(text).filter(Boolean))];
}

function promptPackNeedsRegeneration(value: unknown): boolean {
  if (!isRecord(value)) return false;
  const source = isRecord(value.promptPack) ? value.promptPack : value;
  const hasLegacy = Object.keys(source).some((key) => legacyVisualPackFields.has(key) || legacyMarkers.includes(key));
  const hasNew = newVisualPackFields.some((key) => hasValue(source[key]));
  return hasLegacy && !hasNew;
}

function clean(value: unknown): string {
  let result = text(value).replace(/\s+/g, ' ').trim().replace(/[；，,\s]+$/g, '');
  if (!result || legacyMarkers.some((marker) => result.includes(marker))) return '';
  result = result.replace(internalIdPattern, '');
  return result.replace(/\s{2,}/g, ' ').trim();
}

function geometry(assetClass: string, context: PromptContext, source: PromptRecord): { aspectRatio: string; outputFormat: 'png' } {
  void source;
  const profile = context.assetGenerationProfile || {};
  const projectRatio = text(context.outputAspectRatio || profile.outputAspectRatio || profile.aspect_ratio || '9:16');
  const ratio = assetClass === 'fusion' || assetClass === 'shot' ? projectRatio : baseAssetAspectRatios[assetClass] || '16:9';
  return { aspectRatio: ['16:9', '1:1', '9:16'].includes(ratio) ? ratio : '16:9', outputFormat: 'png' };
}

function fixedLayout(assetClass: string, ratio: string): string {
  if (assetClass === 'character') return '横向四区角色参考板，左侧约42%为角色面部与上半身特写，右侧约58%分为三个等宽全身视图区，从左到右依次为正面全身、严格90°侧面全身、严格180°背面全身；四个区域必须是同一角色，四个视图等高、同尺度、脚底对齐，完整显示头部、双手、双脚和服装下摆。';
  if (assetClass === 'scene') return '横向空环境参考板，清楚呈现前景、中景、背景、空间封口、主要地标和可用动作区域，不放入角色或独立道具。';
  if (assetClass === 'prop') return '正方形独立物件参考图，完整呈现主体轮廓、结构、功能细节、材质状态和尺度参照，不进行人物或场景融合。';
  if (assetClass === 'product') return '正方形产品展示图，产品主体占据视觉中心，完整呈现产品轮廓、材质、包装或关键功能，不让无关道具削弱识别。';
  if (assetClass === 'style') return '横向风格参考板，保持统一的视觉语言、构图节奏、色彩和材质表现。';
  if (assetClass === 'fusion') return `按项目画面比例${ratio}构成一张统一融合图，角色、道具与场景处于同一透视和光线系统中。`;
  if (assetClass === 'shot') return `按项目画面比例${ratio}构成镜头视觉参考图，主体动作和摄影机关系清楚可见。`;
  return `使用${ratio}画面构成完整视觉资产。`;
}

function templateStyle(source: PromptRecord): string {
  const selection = isRecord(source.templateSelection) ? source.templateSelection : {};
  const tags = Array.isArray(selection.visualStyleTags) ? selection.visualStyleTags.map((item) => styleLabels[String(item)] || String(item)).filter(Boolean) : [];
  const guidance = clean(selection.guidance);
  const pitfalls = clean(selection.pitfalls);
  if (!tags.length && !guidance && !pitfalls) return '';
  return `采用${[...new Set(tags)].join('、') || '清晰统一'}视觉语言${guidance ? `；${guidance}` : ''}${pitfalls ? `；模板避坑：${pitfalls}` : ''}。`;
}

function referenceText(value: unknown, context?: PromptContext): string {
  const raw = hasValue(value) ? value : context?.references || [];
  const values = Array.isArray(raw) ? raw : hasValue(raw) ? [raw] : [];
  const parts = values.map((item, index) => {
    if (isRecord(item)) return `已上传参考图${index + 1}用于${clean(item.purpose || item.notes || item.role) || '视觉参考'}，只控制${clean(item.scope || item.controls) || '其声明的视觉范围'}`;
    return `已上传参考图${index + 1}用于${clean(item) || '视觉参考'}`;
  }).filter(Boolean);
  return parts.length ? `${parts.join('；')}。` : '';
}

function shotAction(source: PromptRecord, context: PromptContext, cls: string): string {
  if (cls !== 'fusion' && cls !== 'shot') return '';
  const direct = clean(first(source, ['actionContinuity', 'action_continuity', 'action', 'continuity']));
  if (direct) return direct;
  return (context.shots || []).slice(0, 2).map((shot) => {
    const action = clean(shot.action || shot.purpose);
    const camera = clean(shot.camera || shot.size || shot.framing);
    const continuity = clean(shot.continuity || shot.firstFrame || shot.lastFrame);
    return [action ? `主动作是${action}` : '', camera ? `摄影机保持${camera}` : '', continuity ? `连续性保持${continuity}` : ''].filter(Boolean).join('；');
  }).filter(Boolean).join('；');
}

export function normalizePromptPack(assetClass: string | undefined, rawPack: unknown = {}, options: { identityAnchor?: unknown; mustPreserve?: unknown; mustAvoid?: unknown; context?: PromptContext; templateOverride?: string } = {}): PromptRecord {
  const cls = canonicalAssetClass(assetClass);
  if (cls === 'audio') return { ...(isRecord(rawPack) ? rawPack : {}), schemaVersion: AUDIO_PROMPT_SCHEMA_VERSION, assetType: 'audio' };
  const source = isRecord(rawPack) ? ({ ...(isRecord(rawPack.promptPack) ? rawPack.promptPack : rawPack) }) : {};
  const context = options.context || {};
  const ratio = geometry(cls, context, source);
  const selection = isRecord(source.templateSelection) ? source.templateSelection : {};
  const subject = clean(first(source, ['subjectTask', 'subject_task', 'task', 'goal', 'intent'])) || ({ character: '建立可跨镜头复用的角色视觉身份参考资产', scene: '建立可跨镜头复用的环境与空间参考资产', prop: '建立可复用的独立物件视觉参考资产', product: '建立可复用的产品主体与材质参考资产', fusion: '将已确认的角色、道具和场景组织为同一镜头中的统一画面', shot: '为当前镜头建立可执行的视觉参考画面' }[cls] || '建立一张清晰、可直接用于图像生成的视觉资产参考图');
  const suppliedLayout = clean(first(source, ['compositionLayout', 'composition_layout', 'layout', 'composition']));
  const layout = cls === 'character' ? fixedLayout(cls, ratio.aspectRatio) + (suppliedLayout ? `补充布局要求：${suppliedLayout}。` : '') : fixedLayout(cls, ratio.aspectRatio) + (suppliedLayout ? `补充布局要求：${suppliedLayout}。` : '');
  const visual = clean(first(source, ['visualStyleMaterials', 'visual_style_materials', 'styleDescription', 'appearance'])) || templateStyle(source) || '采用清晰统一、与主体材质相匹配的视觉语言。';
  const labels = clean(first(source, ['textLabels', 'text_labels', 'text', 'labels']));
  const constraints = [
    ...list(first(source, ['constraintsNegative', 'constraints_negative', 'constraints', 'negative', 'negativeDetails'])),
    ...list(options.mustPreserve), ...list(options.mustAvoid),
  ];
  const defaults: Record<string, string> = {
    character: '四个视图保持同一角色的脸部身份、发型、体型、服装结构、材质和配色，不添加第二个角色。',
    scene: '保持空环境，不出现角色、独立道具、融合对象或接触阴影。',
    prop: '保持独立物件边界，不出现人物手部、场景融合或无关道具。',
    product: '保持产品主体完整清晰，不添加无关人物或装饰。',
    style: '保持视觉语言统一，不混入互相冲突的媒介或风格。',
    fusion: '避免拼贴感和贴图感，保持同一透视、接触关系、阴影和材质响应。',
    shot: '保持动作、屏幕方向、主体身份和光线连续。',
  };
  if (defaults[cls] && !constraints.some((item) => item === defaults[cls] || item.includes(defaults[cls]))) constraints.push(defaults[cls]);
  const action = shotAction(source, context, cls);
  const references = isRecord(source.referenceRoles) || Array.isArray(source.referenceRoles) ? source.referenceRoles : context.references || [];
  const pack: PromptRecord = {
    templateSelection: selection,
    subjectTask: subject,
    compositionLayout: layout,
    visualStyleMaterials: visual,
    textLabels: labels,
    aspectRatioOutput: ratio,
    constraintsNegative: [...new Set(constraints.map(clean).filter(Boolean))],
    referenceRoles: Array.isArray(references) ? references : [],
  };
  if (action) pack.actionContinuity = action;
  return pack;
}

export function buildNaturalLanguagePrompt(assetClass: string | undefined, rawPack: unknown, fallbackPrompt = '', context?: PromptContext, _compositionMode: PromptCompositionMode = 'style_library'): string {
  const cls = canonicalAssetClass(assetClass);
  if (cls === 'audio') {
    const packageValue = buildMiniMaxWebPromptPackage(rawPack, fallbackPrompt, context);
    if (packageValue.copyText) return packageValue.copyText;
    if (packageValue.candidateText) return `MiniMax Speech 2.8 Web：候选朗读文本待用户确认：${packageValue.candidateText}`;
    return 'MiniMax Speech 2.8 Web：尚未确认唯一朗读文本，暂不生成。';
  }
  const source = isRecord(rawPack) ? rawPack : {};
  if (promptPackNeedsRegeneration(source)) return '';
  const pack = normalizePromptPack(cls, source, { context });
  if (!hasValue(pack.subjectTask) && fallbackPrompt && !legacyMarkers.some((marker) => fallbackPrompt.includes(marker))) pack.subjectTask = fallbackPrompt;
  const blocks = [
    text(pack.subjectTask), text(pack.compositionLayout), text(pack.visualStyleMaterials), text(pack.textLabels),
    isRecord(pack.aspectRatioOutput) ? `画面比例为${pack.aspectRatioOutput.aspectRatio}，输出为PNG图像资产。` : '',
    referenceText(pack.referenceRoles, context), text(pack.actionContinuity), ...list(pack.constraintsNegative),
  ].map((item) => item.trim().replace(/[。；，,]+$/g, '')).filter(Boolean).map((item) => `${item}。`);
  return [...new Set(blocks)].join('\n\n').trim();
}

export function validateCleanPrompt(prompt: string, assetClass?: string): string[] {
  const value = String(prompt || '').trim();
  const issues = legacyMarkers.filter((marker) => value.includes(marker)).map((marker) => `可复制 Prompt 包含已退役或内部标记：${marker}`);
  if (pixelSizePattern.test(value)) issues.push('可复制 Prompt 不得包含 Provider 像素尺寸');
  if (/[{}[\]]/.test(value)) issues.push('可复制 Prompt 不得包含 JSON 或字段语法');
  if (/(请返回|请上传|请保存|进入下一阶段|调用|Provider|供应商|工作台)/.test(value)) issues.push('可复制 Prompt 不得包含工作流或 Provider 操作指令');
  if (canonicalAssetClass(assetClass) === 'character') {
    for (const token of ['左侧约42%', '右侧约58%', '正面全身', '严格90°侧面全身', '严格180°背面全身']) if (!value.includes(token)) issues.push(`角色四区布局缺少：${token}`);
  }
  return [...new Set(issues)];
}

export function canonicalizePromptOutput(assetClass: string | undefined, rawPack: unknown, prompt: string, context?: PromptContext, _compositionMode: PromptCompositionMode = 'style_library'): { prompt: string; copyablePrompt: string; promptPack: PromptRecord; promptContractVersion: string; promptWorkflow: string; promptQuality: Record<string, unknown>; promptCompositionMode: PromptCompositionMode; promptCompilerVersion: string } {
  const cls = canonicalAssetClass(assetClass);
  if (cls === 'audio') {
    const packageValue = buildMiniMaxWebPromptPackage(rawPack, prompt, context);
    return { prompt: packageValue.copyText || packageValue.candidateText || '', copyablePrompt: packageValue.copyText, promptPack: normalizePromptPack(cls, rawPack), promptContractVersion: AUDIO_PROMPT_SCHEMA_VERSION, promptWorkflow: 'minimax-speech-web', promptQuality: { status: packageValue.copyText ? 'ready' : 'needs-confirmation' }, promptCompositionMode: 'style_library', promptCompilerVersion: 'audio-web-v1' };
  }
  if (promptPackNeedsRegeneration(rawPack)) {
    return { prompt: '', copyablePrompt: '', promptPack: {}, promptContractVersion: PROMPT_CONTRACT_VERSION, promptWorkflow: PROMPT_WORKFLOW_ID, promptQuality: { status: 'needs-regeneration', missing: ['new style-library Prompt Pack'] }, promptCompositionMode: 'style_library', promptCompilerVersion: PROMPT_WORKFLOW_ID };
  }
  const promptPack = normalizePromptPack(cls, rawPack, { context });
  const copyablePrompt = buildNaturalLanguagePrompt(cls, promptPack, prompt, context);
  const issues = validateCleanPrompt(copyablePrompt, cls);
  return { prompt: copyablePrompt, copyablePrompt, promptPack, promptContractVersion: PROMPT_CONTRACT_VERSION, promptWorkflow: PROMPT_WORKFLOW_ID, promptQuality: { status: issues.length ? 'needs-detail' : 'ready', boundaryIssues: issues }, promptCompositionMode: 'style_library', promptCompilerVersion: PROMPT_WORKFLOW_ID };
}

function audioTextStatus(value: unknown, sourceText: string): string {
  if (typeof value === 'boolean') return value && sourceText ? 'confirmed' : sourceText ? 'candidate' : 'missing';
  const normalized = String(value || '').trim().toLowerCase().replaceAll('_', '-').replaceAll(' ', '-');
  if (['confirmed', 'user-confirmed', 'approved', 'locked', 'final'].includes(normalized)) return 'confirmed';
  if (['conflict', 'invalid', 'ambiguous'].includes(normalized)) return 'conflict';
  return sourceText ? 'candidate' : 'missing';
}

function audioSpokenText(value: unknown): string {
  if (typeof value === 'string') return value.trim();
  if (isRecord(value)) for (const key of ['text', 'content', 'line', 'spokenText', 'spoken_text', 'transcript']) if (typeof value[key] === 'string' && String(value[key]).trim()) return String(value[key]).trim();
  if (Array.isArray(value)) return value.map(audioSpokenText).filter(Boolean).join('\n');
  return '';
}

function audioDetails(rawPack: unknown, context?: PromptContext): PromptRecord {
  const source = isRecord(rawPack) ? rawPack : {};
  const raw = isRecord(source.audioDetails) ? { ...source.audioDetails } : {};
  const sourceText = audioSpokenText(raw.sourceText || raw.source_text || raw.spokenText || raw.spoken_text || raw.dialogueText || raw.dialogue_text || raw.line || raw.transcript || raw.text || source.sourceText || source.text);
  const providerText = audioSpokenText(raw.providerText || raw.provider_text || raw.providerInput || raw.provider_input) || sourceText;
  const details: PromptRecord = { ...raw, schemaVersion: AUDIO_PROMPT_SCHEMA_VERSION, sourceText, providerText, textStatus: audioTextStatus(raw.textStatus || raw.text_status, sourceText) };
  const defaults: Record<string, unknown> = { voiceSource: 'system-preset', model: 'speech-2.8-hd', provider: 'minimax', providerRegion: 'cn', speed: 1.0, pitch: 0, volume: 1.0, format: 'wav' };
  for (const [key, value] of Object.entries(defaults)) if (!hasValue(details[key])) details[key] = value;
  if (!hasValue(details.languageBoost)) {
    const locale = String(details.locale || '').toLowerCase().replaceAll('_', '-');
    const language = String(details.language || '');
    details.languageBoost = audioLocaleLanguageBoosts[locale] || audioLocaleLanguageBoosts[locale.split('-', 1)[0]] || (language.includes('日') || language === 'Japanese' ? 'Japanese' : language.includes('中') || language === 'Chinese' ? 'Chinese' : null);
  }
  details.relevantShots = Array.isArray(details.relevantShots) ? details.relevantShots : (context?.shots || []).map((shot) => String(shot.id || shot.shotId || shot.shot_id || '')).filter(Boolean);
  details.continuityChecklist = source.continuityChecklist || source.continuity_checklist || [];
  details.mustPreserve = source.mustPreserve || source.must_preserve || [];
  details.mustAvoid = source.mustAvoid || source.must_avoid || [];
  return details;
}

export function buildMiniMaxWebPromptPackage(rawPack: unknown, fallbackPrompt = '', context?: PromptContext): MiniMaxWebPromptPackage {
  const details = audioDetails(rawPack, context);
  let sourceText = audioSpokenText(details.sourceText);
  let providerText = audioSpokenText(details.providerText) || sourceText;
  let status = audioTextStatus(details.textStatus, sourceText);
  if (!sourceText && fallbackPrompt.trim()) { sourceText = fallbackPrompt.trim(); providerText = sourceText; status = 'candidate'; }
  const candidates = (context?.shots || []).map((shot) => ({ shotId: String(shot.id || shot.shotId || shot.shot_id || ''), kind: shot.narration || shot.voiceover ? '旁白' : '对白', text: audioSpokenText(shot.dialogue || shot.dialogues || shot.narration || shot.voiceover || shot.voice_over || shot.line || shot.lines) })).filter((item) => item.text);
  const shotIds = (context?.shots || []).map((shot) => String(shot.id || shot.shotId || shot.shot_id || '')).filter(Boolean);
  const warnings: string[] = [];
  if (status !== 'confirmed') warnings.push('朗读文本尚未标记为 confirmed；请先确认每个镜头的唯一台词，再复制到 MiniMax Web。');
  if (new Set(candidates.map((item) => item.text)).size > 1) warnings.push('关联镜头存在多条不同文本；必须拆成多次生成，不能拼成一段。');
  if (shotIds.length > candidates.length && candidates.length) warnings.push('部分关联镜头没有明确朗读文本；请逐镜头确认台词或明确该镜头无对白。');
  if (status === 'conflict') warnings.push('当前文本存在镜头/台词冲突，暂不提供可复制的朗读文本。');
  const direction = [details.voiceIdentity, details.language, details.dialect, details.performanceDirection, details.emotion ? `情绪为${details.emotion}` : '', details.intensity ? `强度为${details.intensity}` : '', details.pace ? `语速为${details.pace}` : '', details.distance ? `投射距离为${details.distance}` : ''].map(text).filter(Boolean).join('；');
  return {
    schemaVersion: AUDIO_PROMPT_SCHEMA_VERSION, provider: 'minimax', operation: text(details.operation) || 'tts', sourceText, providerText,
    copyText: providerText && audioConfirmedTextStatuses.has(status) ? providerText : '', candidateText: providerText && !audioConfirmedTextStatuses.has(status) ? providerText : '', textStatus: status,
    direction, settings: { provider: 'minimax', model: text(details.model) || 'speech-2.8-hd', voiceId: text(details.providerVoiceId || details.voiceId) || '在 MiniMax Web 中选择固定系统音色', voiceName: text(details.providerVoiceName) || '以实际试听结果为准', region: text(details.providerRegion) || 'cn', languageBoost: text(details.languageBoost) || '自动识别', emotion: text(details.emotion) || '留空', speed: text(details.speed) || '1.0', pitch: text(details.pitch) || '0', volume: text(details.volume) || '1.0', format: text(details.format) || 'wav' },
    pausePlan: details.pausePlan || [], pronunciation: details.pronunciation || {}, soundTags: details.soundTags || [], targetDuration: details.targetDuration, relevantShots: details.relevantShots || shotIds, candidates, continuity: Array.isArray(details.continuityChecklist) ? details.continuityChecklist.map(text).filter(Boolean) : [], mustPreserve: list(details.mustPreserve), mustAvoid: list(details.mustAvoid), warnings,
  };
}

export function formatMiniMaxWebPromptPackage(packageValue: MiniMaxWebPromptPackage, assetName = '', assetId = ''): string {
  const pauseText = text(packageValue.pausePlan); const pronunciationText = text(packageValue.pronunciation); const soundTagText = text(packageValue.soundTags);
  return [
    `MiniMax Speech 2.8 Web 测试包${assetName ? ` · ${assetName}` : ''}`,
    '【只有这一段可以粘贴到 MiniMax 文本框】', packageValue.copyText || packageValue.candidateText || '（尚未形成可复制朗读文本）',
    '【MiniMax Web 设置】', `音色：${packageValue.settings.voiceId}`, `语言增强：${packageValue.settings.languageBoost}`, `情绪：${packageValue.settings.emotion}`, `语速：${packageValue.settings.speed}`, `音调：${packageValue.settings.pitch}`, `音量：${packageValue.settings.volume}`,
    packageValue.direction ? `表演方向：${packageValue.direction}` : '', pauseText ? `停顿计划：${pauseText}` : '', pronunciationText ? `发音标注：${pronunciationText}` : '', soundTagText ? `声音标签：${soundTagText}` : '',
    '【工作台信息｜不要粘贴到 MiniMax】', assetId ? `资产：${assetId}` : '', hasValue(packageValue.relevantShots) ? `关联镜头：${text(packageValue.relevantShots)}` : '', packageValue.warnings.length ? `提醒：${packageValue.warnings.join('；')}` : '',
  ].filter(Boolean).join('\n');
}

export function renderPromptValue(value: unknown): string { return text(value); }
