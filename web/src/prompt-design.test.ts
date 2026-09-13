import { describe, expect, it } from 'vitest';
import {
  buildMiniMaxWebPromptPackage,
  buildNaturalLanguagePrompt,
  canonicalizePromptOutput,
  formatMiniMaxWebPromptPackage,
  normalizePromptPack,
  validateCleanPrompt,
} from './prompt-design';

describe('style-library visual Prompt boundary', () => {
  it('normalizes only the new visual blocks and preserves the fixed character sheet', () => {
    const pack = normalizePromptPack('character', {
      subjectTask: '一名冷白科幻驾驶员',
      visualStyleMaterials: '写实动漫融合，冷白装甲、石墨黑结构、青蓝发光接口',
      textLabels: '',
      referenceRoles: [{ referenceId: 'C001', purpose: '锁定角色身份', scope: '脸部和服装' }],
    });
    expect(Object.keys(pack)).toEqual([
      'templateSelection',
      'subjectTask',
      'compositionLayout',
      'visualStyleMaterials',
      'textLabels',
      'aspectRatioOutput',
      'constraintsNegative',
      'referenceRoles',
    ]);
    const prompt = buildNaturalLanguagePrompt('character', pack);
    expect(prompt).toContain('左侧约42%为角色面部与上半身特写');
    expect(prompt).toContain('右侧约58%分为三个等宽全身视图区');
    expect(prompt).toContain('正面全身');
    expect(prompt).toContain('严格90°侧面全身');
    expect(prompt).toContain('严格180°背面全身');
    expect(prompt).toContain('画面比例为16:9');
    expect(prompt).toContain('输出为PNG图像资产');
    expect(prompt).not.toContain('C001');
    expect(prompt).not.toContain('character-design-sheet');
    expect(prompt).not.toContain('Prompt Contract');
    expect(validateCleanPrompt(prompt, 'character')).toEqual([]);
  });

  it('keeps scene, prop, product and project-level fusion ratios distinct', () => {
    const cases: Array<[string, string, Record<string, unknown>]> = [
      ['scene', '16:9', { subjectTask: '雨夜山腰祠堂空环境', visualStyleMaterials: '写实摄影，湿石材和旧木' }],
      ['prop', '1:1', { subjectTask: '六翼折叠机械道具', visualStyleMaterials: '磨砂钛灰与黑色橡胶接缝' }],
      ['product', '1:1', { subjectTask: '透明护肤瓶', visualStyleMaterials: '商业产品摄影，玻璃和金属高光' }],
      ['fusion', '16:9', { subjectTask: '角色握住机械道具站在祠堂前', visualStyleMaterials: '统一写实摄影', actionContinuity: '角色从左向右迈步，保持屏幕方向连续' }],
    ];
    for (const [assetClass, ratio, rawPack] of cases) {
      const prompt = buildNaturalLanguagePrompt(assetClass, rawPack, '', { outputAspectRatio: '16:9' });
      expect(prompt).toContain('画面比例为' + ratio);
      expect(prompt).toContain('输出为PNG图像资产');
      expect(prompt).not.toContain('1536x1024');
      expect(prompt).not.toContain('1024x1024');
      expect(prompt).not.toContain('OpenAI');
      expect(prompt).not.toContain('JSON');
    }
    const shot = normalizePromptPack('shot', { subjectTask: '镜头关键帧', actionContinuity: '摄影机低机位跟随主体' }, { context: { outputAspectRatio: '9:16' } });
    expect(shot.aspectRatioOutput).toEqual({ aspectRatio: '9:16', outputFormat: 'png' });
  });

  it('renders references as visual roles without leaking IDs or internal metadata', () => {
    const prompt = buildNaturalLanguagePrompt('prop', {
      subjectTask: '独立机械道具',
      visualStyleMaterials: '清晰展示结构和材质',
      referenceRoles: [{ referenceId: 'P02', role: 'connected asset', purpose: '锁定接口与比例', scope: '道具结构' }],
    });
    expect(prompt).toContain('已上传参考图1用于锁定接口与比例，只控制道具结构');
    expect(prompt).not.toContain('P02');
    expect(prompt).not.toContain('referenceId');
  });

  it('never uses retired visual fields or old prompt text as a frontend fallback', () => {
    const prompt = buildNaturalLanguagePrompt('scene', {
      promptIntent: '旧版意图',
      identityAnchor: '旧版身份',
      sceneDetails: { geography: '旧版空间' },
    }, '旧 Prompt 全文\n\n同时满足以下补充制作要求：旧规则');
    expect(prompt).not.toContain('旧 Prompt 全文');
    expect(prompt).not.toContain('同时满足以下补充制作要求');
    expect(prompt).not.toContain('旧版身份');
    expect(prompt).not.toContain('identityAnchor');
    expect(canonicalizePromptOutput('scene', { promptIntent: '旧版意图', sceneDetails: { geography: '旧版空间' } }, '旧 Prompt 全文').copyablePrompt).toBe('');
  });

  it('keeps the MiniMax Web audio package independent from visual Prompt rules', () => {
    const pack = {
      audioDetails: {
        sourceText: '看招。',
        textStatus: 'candidate',
        voiceIdentity: '成年女性中文普通话，低沉、冷峻',
        performanceDirection: '咬字清楚，句尾收住',
        language: '中文',
        dialect: '普通话',
      },
    };
    const prompt = buildNaturalLanguagePrompt('audio', pack);
    const packageValue = buildMiniMaxWebPromptPackage(pack, '', { shots: [{ id: 'S03', dialogue: '看招。' }, { id: 'S16' }] });
    expect(packageValue.textStatus).toBe('candidate');
    expect(packageValue.copyText).toBe('');
    expect(packageValue.candidateText).toBe('看招。');
    expect(prompt).toContain('候选朗读文本待用户确认');
    expect(prompt).not.toContain('空间关系与地理');
    expect(prompt).not.toContain('FRAMEFLOW');
  });

  it('exposes only confirmed text as MiniMax copy text', () => {
    const packageValue = buildMiniMaxWebPromptPackage({ audioDetails: { sourceText: '看招。<#0.35#>', textStatus: 'confirmed' } });
    expect(packageValue.copyText).toBe('看招。<#0.35#>');
    expect(packageValue.candidateText).toBe('');
  });

  it('keeps MiniMax source/provider text and derives Japanese language boost', () => {
    const packageValue = buildMiniMaxWebPromptPackage({ audioDetails: {
      sourceText: '先輩、今日の放課後、一緒に帰りませんか？',
      providerText: '先輩、今日の放課後、(breath) 一緒に帰りませんか？',
      textStatus: 'confirmed',
      locale: 'ja-JP',
      language: 'Japanese',
      providerVoiceId: 'Japanese_SportyStudent',
      providerRegion: 'cn',
    } });
    expect(packageValue.sourceText).not.toContain('(breath)');
    expect(packageValue.providerText).toContain('(breath)');
    expect(packageValue.copyText).toBe(packageValue.providerText);
    expect(packageValue.settings.languageBoost).toBe('Japanese');
  });

  it('keeps MiniMax settings and workflow notices outside the pasted text block', () => {
    const packageValue = buildMiniMaxWebPromptPackage({ audioDetails: { textStatus: 'missing', voiceIdentity: '成年女性中文普通话' } }, '', {
      shots: [{ id: 'S03', dialogue: '看招。' }, { id: 'S16' }],
    });
    const rendered = formatMiniMaxWebPromptPackage(packageValue, 'AUD02', 'AUD02');
    expect(rendered).toContain('只有这一段可以粘贴到 MiniMax 文本框');
    expect(rendered).toContain('S03');
    expect(rendered).toContain('S16');
    expect(rendered).toContain('不要粘贴到 MiniMax');
  });
});
