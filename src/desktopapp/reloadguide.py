"""User-visible cold reload steps, shared by the log and completion dialog."""

STEPS = (
    '仅在软件明确显示“读写已结束”后操作。\n\n'
    '1. 拔掉相机 USB 数据线，并断开其他外部供电。\n'
    '2. 等待相机存取灯停止闪烁，不要在灯闪烁时取电池。\n'
    '3. 将相机电源拨到 OFF，等屏幕和存取灯完全熄灭。\n'
    '4. 取下电池，让相机同时没有电池、USB 和其他供电，至少等待 1 分钟。\n'
    '5. 装回电池并开机。'
)

WAITING_PHASES = {'WAIT_RELOAD', 'AWAITING_RELOAD', 'RESTORED_AWAITING_RELOAD',
                  'installed_pending_cold_start','WAIT_RESOURCE_RELOAD','AWAITING_RESOURCE_RELOAD'}
SOUND_PHASES = {
    'sound_on': {'written'}, 'sound_off': {'restored'},
    'sound_install': {'installed_cold_test_pending'},
    'sound_restore_sound': {'restored_cold_test_pending'},
    'sound_confirm': set(),
}


def required(action, result):
    """Use completed backend outcomes, never guess from a write button name."""
    phase = result.get('phase')
    if result.get('reload_required') is True:
        return True
    if phase in WAITING_PHASES:
        return True
    return (phase in SOUND_PHASES.get(action, set())
            and not result.get('adopted_existing_enabled'))


def sound_notice(action,result):
    """Temporary audition needs guidance while the current power stays on."""
    phase=result.get('phase')
    if action=='sound_audition' and phase=='temporary_pcm_registered_cold_reload_required_after_test':
        return dict(title='试听已准备好，请保持相机开机',
            status='试听已准备好。拔 USB 并保持开机，试拍后接回即可直接保存。',
            text='相机读写已结束。当前声音只供临时试听，尚未永久保存。\n\n'
                 '1. 拔掉 USB，保持相机开机；不要关机、取下电池或更改音频信号设置。\n'
                 '2. 使用电子快门拍一张，检查声音内容、音量、音调／速度，以及拍摄和回放是否正常。\n'
                 '3. 接回 USB 海量存储，点击“保存当前自定义声音”。可以直接保存，无需先恢复原声。\n'
                 '4. 保存写入完成后，再按弹窗完整断电重开，检查是否永久生效。\n\n'
                 '“确认试听正确”只记录试听结果，是可选步骤。\n'
                 '本弹窗的“确定”只关闭说明，不代表已确认试听正确。')
    if action=='sound_confirm' and phase in ('owner_confirmed_audio_cold_reload_required',
            'owner_audio_failed_cold_reload_required','owner_requested_gain_adjustment_cold_reload_required'):
        return dict(title='试听结果已记录',status='试听记录已保存；可直接保存当前自定义声音，无需先断电恢复。',
                    text='这一步只记录试听结果。\n\n可直接点击“保存当前自定义声音”，无需先断电或记录恢复。'
                    '若不满意，调整片段后重新转换；需要清除临时试听时，再按断电步骤恢复原声。')
    if action!='sound_install':return None
    if phase=='sound_conversion_required':
        return dict(title='保存尚未开始，请先转换片段',status='等待操作：选择声音文件，转换后即可直接保存。',
                    text='尚无可保存的转换片段，本次没有相机写入。\n\n选择音频或视频，设置起点和长度，'
                    '点击“转换所选片段”；转换成功后直接点击“保存当前自定义声音”。试听是可选步骤。')
    return None


def text(*, setup=False, mode=None):
    if mode=='resource_reload':
        return ('名称阶段已完成，程序尚未写入。旧资源仍被相机占用，只读挂载尚未恢复；需要先释放旧资源，再继续剩余安装。\n\n'+STEPS+
            '\n\n开机后先不用拍照。接回 USB 海量存储，再点'+('首页“一键安装／继续上次安装”' if setup else '自定义外观页“写入／继续已选外观”')+
            '。工具会核对新的冷启动和只读挂载，然后继续剩余程序，不重复写名称、不重装驱动。\n\n程序写完后还会提示最终重开，让新功能生效。点确定只关闭说明。')
    reason = ('\n\n这次“启用 FL2／FL3”已写入程序文件。此前恢复原厂后的重开只加载了原厂状态；本次新的修改需要再次重开才能生效。'
              if mode == 'fl23_enable' else '')
    follow = ('接回 USB，选择海量存储，再点首页“一键安装／继续上次安装”。工具先核对加载，不重复刷写。'
              if setup else '在相机中确认 FL2／FL3 能选择、拍摄及回放，即可使用。不必再接电脑点击核对；如需排查，可使用 FL23 页的可选诊断。'
              if mode in ('fl23_enable', 'fl23_disable') else
              '此次断电仅用于清除临时试听、恢复原声，不是保存声音的前置条件。开机确认原声、拍摄及回放正常，可点声音页“已断电恢复原声，记录恢复完成”。保存当前转换片段不需要先执行这一步。'
              if mode == 'sound_confirm' else
              '开机后用电子快门拍摄，检查声音、音量及拍摄／回放。保存自定义声音后，可在声音页核对加载状态。'
              if mode and mode.startswith('sound_') else
              '竖屏开关和资源已保存。重开后分别左右竖握检查拍摄信息；无需每次重新连接电脑开启。不是整个 MENU 转向。'
              if mode == 'vertical_enable' else
              '竖屏开关已保存关闭，辅助资源已移除。重开后确认横握／竖握显示及拍摄正常。'
              if mode == 'vertical_disable' else
              '确认能正常取景，再检查菜单／外观预览，并拍一张、回放。接回 USB 海量存储后，点对应页面的加载核对按钮；只有实际测试正常后才勾选确认项。')
    return STEPS + reason + '\n\n下一步：' + follow + '\n\n加载核对只读取状态，不会再刷一次。点“确定”只关闭说明，不会自动断电或代替你确认测试。'
