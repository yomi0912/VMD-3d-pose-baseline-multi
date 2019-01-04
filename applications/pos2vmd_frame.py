#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from PyQt5.QtGui import QQuaternion, QVector4D, QVector3D, QMatrix4x4
import logging

from VmdWriter import VmdBoneFrame

logger = logging.getLogger("pos2vmd_multi").getChild(__name__)


# 3D推定位置から関節角度生成
def position_to_frame(bone_frame_dic, pos, pos_gan, smoothed_2d, frame, xangle, is_upper2_body):
    logger.debug("角度計算 frame={0}".format(str(frame)))

	# 補正角度のクォータニオン
    decrease_correctqq = QQuaternion.fromEulerAngles(QVector3D(xangle * 0.7, 0, 0))
    increase_correctqq = QQuaternion.fromEulerAngles(QVector3D(xangle * 1.7, 0, 0))
    increase2_correctqq = QQuaternion.fromEulerAngles(QVector3D(xangle * 2, 0, 0))
    normal_correctqq = QQuaternion.fromEulerAngles(QVector3D(xangle, 0, 0))

    # 体幹の回転
    upper_body_rotation1, upper_body_rotation2, upper_correctqq, lower_body_rotation, lower_correctqq, is_gan \
        = position_to_frame_trunk(bone_frame_dic, frame, pos, pos_gan, is_upper2_body, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq)

    # 上半身
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8f\xe3\x94\xbc\x90\x67' # '上半身'
    bf.rotation = upper_body_rotation1
    bone_frame_dic["上半身"].append(bf)

    # 上半身2(角度がある場合のみ登録)
    if upper_body_rotation2 != QQuaternion():
        bf = VmdBoneFrame(frame)
        bf.name = b'\x8f\xe3\x94\xbc\x90\x67\x32' # '上半身2'
        bf.rotation = upper_body_rotation2
        bone_frame_dic["上半身2"].append(bf)

    # 下半身
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\xba\x94\xbc\x90\x67' # '下半身'
    bf.rotation = lower_body_rotation
    bone_frame_dic["下半身"].append(bf)

    neck_rotation, head_rotation = \
        position_to_frame_head(frame, pos, pos_gan, upper_body_rotation1, upper_body_rotation2, upper_correctqq, is_gan)

    # 首
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8e\xf1' # '首'
    bf.rotation = neck_rotation
    bone_frame_dic["首"].append(bf)

    # 頭
    bf = VmdBoneFrame(frame)
    bf.name = b'\x93\xaa' # '頭'
    bf.rotation = head_rotation
    bone_frame_dic["頭"].append(bf)

    # 左肩の初期値
    gan_left_shoulder_initial_orientation = QQuaternion.fromDirection(QVector3D(1, 0, 0), QVector3D(0, 1, 0))
    left_shoulder_initial_orientation = QQuaternion.fromDirection(QVector3D(2, -0.8, 0), QVector3D(0.5, -0.5, -1))
    left_arm_initial_orientation = QQuaternion.fromDirection(QVector3D(1.73, -1, 0), QVector3D(1, 1.73, 0))

    # 左手系の回転
    left_shoulder_rotation, left_arm_rotation, left_elbow_rotation = \
        position_to_frame_arm_one_side(frame, pos, pos_gan, upper_correctqq, upper_body_rotation1, upper_body_rotation2, gan_left_shoulder_initial_orientation, left_shoulder_initial_orientation, left_arm_initial_orientation, LEFT_POINT, is_gan)

    # 左肩
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x8C\xA8' # '左肩'
    bf.rotation = left_shoulder_rotation
    bone_frame_dic["左肩"].append(bf)
    
    # 左腕
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x98\x72' # '左腕'
    bf.rotation = left_arm_rotation
    bone_frame_dic["左腕"].append(bf)
    
    # 左ひじ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x82\xd0\x82\xb6' # '左ひじ'
    bf.rotation = left_elbow_rotation
    bone_frame_dic["左ひじ"].append(bf)
    
    # 右肩の初期値
    gan_right_shoulder_initial_orientation = QQuaternion.fromDirection(QVector3D(-1, 0, 0), QVector3D(0, -1, 0))
    right_shoulder_initial_orientation = QQuaternion.fromDirection(QVector3D(-2, -0.8, 0), QVector3D(0.5, 0.5, 1))
    right_arm_initial_orientation = QQuaternion.fromDirection(QVector3D(-1.73, -1, 0), QVector3D(1, -1.73, 0))

    # 右手系の回転
    right_shoulder_rotation, right_arm_rotation, right_elbow_rotation = \
        position_to_frame_arm_one_side(frame, pos, pos_gan, upper_correctqq, upper_body_rotation1, upper_body_rotation2, gan_right_shoulder_initial_orientation, right_shoulder_initial_orientation, right_arm_initial_orientation, RIGHT_POINT, is_gan)
    
    # 右肩
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x8C\xA8' # '右肩'
    bf.rotation = right_shoulder_rotation
    bone_frame_dic["右肩"].append(bf)
    
    # 右腕
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x98\x72' # '右腕'
    bf.rotation = right_arm_rotation
    bone_frame_dic["右腕"].append(bf)
    
    # 右ひじ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x82\xd0\x82\xb6' # '右ひじ'
    bf.rotation = right_elbow_rotation
    bone_frame_dic["右ひじ"].append(bf)

    # 左足と左ひざの回転
    left_leg_rotation, left_knee_rotation = \
        position_to_frame_leg_one_side(frame, pos, pos_gan, lower_correctqq, lower_body_rotation, LEFT_POINT, ["左足", "左ひざ"], is_gan)

    # 左足
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x91\xab' # '左足'
    bf.rotation = left_leg_rotation
    bone_frame_dic["左足"].append(bf)
    
    # 左ひざ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x82\xd0\x82\xb4' # '左ひざ'
    bf.rotation = left_knee_rotation
    bone_frame_dic["左ひざ"].append(bf)

    # 右足と右ひざの回転
    right_leg_rotation, right_knee_rotation = \
        position_to_frame_leg_one_side(frame, pos, pos_gan, lower_correctqq, lower_body_rotation, RIGHT_POINT, ["右足", "右ひざ"], is_gan)

    # 右足
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x91\xab' # '右足'
    bf.rotation = right_leg_rotation
    bone_frame_dic["右足"].append(bf)
    
    # 右ひざ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x82\xd0\x82\xb4' # '右ひざ'
    bf.rotation = right_knee_rotation
    bone_frame_dic["右ひざ"].append(bf)
        
    # センター(箱だけ作る)
    bf = VmdBoneFrame(frame)
    bf.name = b'\x83\x5A\x83\x93\x83\x5E\x81\x5B' # 'センター'
    bone_frame_dic["センター"].append(bf)

    # グルーブ(箱だけ作る)
    bf = VmdBoneFrame(frame)
    bf.name = b'\x83\x4F\x83\x8B\x81\x5B\x83\x75' # 'グルーブ'
    bone_frame_dic["グルーブ"].append(bf)

    # 左足ＩＫ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x91\xab\x82\x68\x82\x6a' # '左足ＩＫ'
    bone_frame_dic["左足ＩＫ"].append(bf)

    # 右足ＩＫ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x91\xab\x82\x68\x82\x6a' # '右足ＩＫ'
    bone_frame_dic["右足ＩＫ"].append(bf)

# 右系のpos point
RIGHT_POINT = {
    'Hip': 1,
    'Knee': 2,
    'Foot': 3,
    'Thorax': 8,
    'Shoulder': 14,
    'Elbow': 15,
    'Wrist': 16,
    'AnotherShoulder': 11
}
# 左系のpos point
LEFT_POINT = {
    'Hip': 4,
    'Knee': 5,
    'Foot': 6,
    'Thorax': 8,
    'Shoulder': 11,
    'Elbow': 12,
    'Wrist': 13,
    'AnotherShoulder': 14
}

def position_to_frame_head(frame, pos, pos_gan, upper_body_rotation1, upper_body_rotation2, upper_correctqq, is_gan):
    if is_gan: 
        # 体幹が3dpose-ganで決定されている場合

        # 首
        direction = pos[9] - pos[8]
        up = QVector3D.crossProduct((pos[14] - pos[11]), direction).normalized()
        neck_orientation = QQuaternion.fromDirection(up, direction)
        initial_orientation = QQuaternion.fromDirection(QVector3D(0, 0, -1), QVector3D(0, 1, 0))
        rotation = neck_orientation * initial_orientation.inverted()
        neck_rotation = upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation

        # 頭
        direction = pos[10] - pos[9]
        up = QVector3D.crossProduct((pos[14] - pos[11]), (pos[10] - pos[9]))
        orientation = QQuaternion.fromDirection(direction, up)
        initial_orientation = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(0, 0, 0))
        rotation = upper_correctqq * orientation * initial_orientation.inverted()
        head_rotation = neck_rotation.inverted() * upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation

    else:
        # 体幹が 3d-pose-baseline で決定されている場合

        # 首
        direction = pos[9] - pos[8]
        up = QVector3D.crossProduct((pos[14] - pos[11]), direction).normalized()
        neck_orientation = QQuaternion.fromDirection(up, direction)
        initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(0, 0, -1))
        rotation = neck_orientation * initial_orientation.inverted()
        neck_rotation = upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation

        # 頭
        direction = pos[10] - pos[9]
        up = QVector3D.crossProduct((pos[9] - pos[8]), (pos[10] - pos[9]))
        orientation = QQuaternion.fromDirection(direction, up)
        initial_orientation = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(1, 0, 0))
        rotation = upper_correctqq * orientation * initial_orientation.inverted()
        head_rotation = neck_rotation.inverted() * upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation

    return neck_rotation, head_rotation

def is_smoothed_prev_frame(bone_frame_dic, frame, bone_rotation_dic, angle):
    # 最初は問答無用でOK
    if frame == 0:
        return True

    for bone_name, bone_rotation in bone_rotation_dic.items():    
        if len(bone_frame_dic[bone_name]) > frame-1:
            # 1F前の回転との差分をチェックする
            prev_euler = bone_frame_dic[bone_name][frame-1].rotation.toEulerAngles()
            now_euler = bone_rotation.toEulerAngles()

            if abs(prev_euler.x() - now_euler.x()) > angle \
                or abs(prev_euler.y() - now_euler.y()) > angle \
                or abs(prev_euler.z() - now_euler.z()) > angle :
                return False
    
    return True

def position_to_frame_trunk(bone_frame_dic, frame, pos, pos_gan, is_upper2_body, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq):

    if pos_gan is not None:
        # 3dpose-gan による上半身FK
        g_upper_body_rotation1, g_upper_body_rotation2, g_upper_correctqq \
            = position_to_frame_upper_calc(frame, pos_gan, is_upper2_body, QQuaternion(), QQuaternion(), QQuaternion(), QQuaternion())
        # 3dpose-gan による下半身FK
        g_lower_body_rotation, g_lower_correctqq \
            = position_to_frame_lower_calc(frame, pos_gan, QQuaternion(), QQuaternion(), QQuaternion(), QQuaternion())

        # 前フレームとの差が45度以内で、オイラー角回転がどれか45度以上の場合、3dpose-gan採用
        # 体幹はY軸回転は見ない
        if is_smoothed_prev_frame(bone_frame_dic, frame, { "上半身":g_upper_body_rotation1, "上半身2": g_upper_body_rotation2, "下半身":g_lower_body_rotation }, 45) \
            and (abs(g_upper_body_rotation1.toEulerAngles().x()) > 45 or abs(g_upper_body_rotation1.toEulerAngles().z()) > 45 \
                or abs(g_lower_body_rotation.toEulerAngles().x()) > 45 or abs(g_lower_body_rotation.toEulerAngles().z()) > 45 ):

            # # Zを反転させる
            # g_upper_body_rotation1.setZ( g_upper_body_rotation1.z() * -1 )
            # g_lower_body_rotation.setZ( g_lower_body_rotation.z() * -1 )
            
            logger.debug("gan採用: %s u1=%s u2=%s l=%s", frame, g_upper_body_rotation1, g_upper_body_rotation2, g_lower_body_rotation)

            return g_upper_body_rotation1, g_upper_body_rotation2, g_upper_correctqq, g_lower_body_rotation, g_lower_correctqq, True

    # 3d-pose-baseline による上半身FK
    upper_body_rotation1, upper_body_rotation2, upper_correctqq \
        = position_to_frame_upper_calc(frame, pos, is_upper2_body, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq)
        
    # 3d-pose-baseline による下半身FK
    lower_body_rotation, lower_correctqq \
        = position_to_frame_lower_calc(frame, pos, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq)

    return upper_body_rotation1, upper_body_rotation2, upper_correctqq, lower_body_rotation, lower_correctqq, False


# 上半身FK（実質計算用）
def position_to_frame_upper_calc(frame, pos, is_upper2_body, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq):

    if is_upper2_body == True:
        # 上半身2がある場合、分割して登録する

        # 上半身
        direction = pos[7] - pos[0]
        up = QVector3D.crossProduct(direction, (pos[14] - pos[11])).normalized()
        upper_body_orientation = QQuaternion.fromDirection(direction, up)
        initial = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(0, 0, 1))
        upper_body_rotation1 = upper_body_orientation * initial.inverted()

        # 補正をかけて回転する
        if upper_body_rotation1.toEulerAngles().y() < 30 and upper_body_rotation1.toEulerAngles().y() > -30:
            # 前向きは増量補正
            upper_correctqq = increase_correctqq
        elif upper_body_rotation1.toEulerAngles().y() < -120 or upper_body_rotation1.toEulerAngles().y() > 120:
            # 後ろ向きは通常補正
            upper_correctqq = normal_correctqq
        else:
            # 横向きは減少補正
            upper_correctqq = decrease_correctqq

        upper_body_rotation1 = upper_body_rotation1 * upper_correctqq

        # 上半身2
        direction = pos[8] - pos[7]
        up = QVector3D.crossProduct(direction, (pos[14] - pos[11])).normalized()
        upper_body_orientation = QQuaternion.fromDirection(direction, up)
        initial = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(0, 0, 1))
        upper_body_rotation2 = upper_body_orientation * initial.inverted()

        # 補正をかけて回転する
        if upper_body_rotation2.toEulerAngles().y() < 30 and upper_body_rotation2.toEulerAngles().y() > -30:
            # 前向きは増量大補正
            upper_correctqq = increase_correctqq
        elif upper_body_rotation2.toEulerAngles().y() < -120 or upper_body_rotation2.toEulerAngles().y() > 120:
            # 後ろ向きは増量補正
            upper_correctqq = normal_correctqq
        else:
            # 横向きは通常補正
            upper_correctqq = decrease_correctqq

        upper_body_rotation2 = upper_body_rotation1.inverted() * upper_body_rotation2 * upper_correctqq
        
    else:
        # 上半身2は初期クォータニオン
        upper_body_rotation2 = QQuaternion()
        
        """convert positions to bone frames"""
        # 上半身
        direction = pos[8] - pos[7]
        up = QVector3D.crossProduct(direction, (pos[14] - pos[11])).normalized()
        upper_body_orientation = QQuaternion.fromDirection(direction, up)
        initial = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(0, 0, 1))
        upper_body_rotation1 = upper_body_orientation * initial.inverted()

        # 補正をかけて回転する
        if upper_body_rotation1.toEulerAngles().y() < 30 and upper_body_rotation1.toEulerAngles().y() > -30:
            # 前向きは増量補正
            upper_correctqq = increase_correctqq
        elif upper_body_rotation1.toEulerAngles().y() < -120 or upper_body_rotation1.toEulerAngles().y() > 120:
            # 後ろ向きは通常補正
            upper_correctqq = normal_correctqq
        else:
            # 横向きは減少補正
            upper_correctqq = decrease_correctqq

        upper_body_rotation1 = upper_body_rotation1 * upper_correctqq
           
    return upper_body_rotation1, upper_body_rotation2, upper_correctqq

# 下半身FK（実質計算用）
def position_to_frame_lower_calc(frame, pos, decrease_correctqq, increase_correctqq, increase2_correctqq, normal_correctqq):
    direction = pos[0] - pos[7]
    up = QVector3D.crossProduct(direction, (pos[4] - pos[1]))
    lower_body_orientation = QQuaternion.fromDirection(direction, up)
    initial = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(0, 0, 1))
    lower_body_rotation = lower_body_orientation * initial.inverted()

    # 補正をかけて回転する
    if lower_body_rotation.toEulerAngles().y() < 30 and lower_body_rotation.toEulerAngles().y() > -30:
        # 前向きは通常補正
        lower_correctqq = normal_correctqq
    elif lower_body_rotation.toEulerAngles().y() < -120 or lower_body_rotation.toEulerAngles().y() > 120:
        # 後ろ向きは通常補正
        lower_correctqq = normal_correctqq
    else:
        # 横向きは減少補正
        lower_correctqq = decrease_correctqq

    lower_body_rotation = lower_body_rotation * lower_correctqq

    return lower_body_rotation, lower_correctqq

# 片手のFK
def position_to_frame_arm_one_side(frame, pos, pos_gan, upper_correctqq, upper_body_rotation1, upper_body_rotation2, gan_shoulder_initial_orientation, shoulder_initial_orientation, arm_initial_orientation, points, is_gan):

    if pos_gan is not None and is_gan == True:

        # 手(3dpose-gan採用)
        return position_to_frame_shoulder_one_side_calc(frame, pos_gan, QQuaternion(), upper_body_rotation1, upper_body_rotation2, gan_shoulder_initial_orientation, arm_initial_orientation, points)

    # 3d-pose-baseline の手FK
    return position_to_frame_shoulder_one_side_calc(frame, pos, upper_correctqq, upper_body_rotation1, upper_body_rotation2, shoulder_initial_orientation, arm_initial_orientation, points)


# 片方の手FKの実体
def position_to_frame_shoulder_one_side_calc(frame, pos, upper_correctqq, upper_body_rotation1, upper_body_rotation2, shoulder_initial_orientation, arm_initial_orientation, points):

    # 肩
    direction = pos[points['Shoulder']] - pos[points['Thorax']]
    up = QVector3D.crossProduct((pos[points['Shoulder']] - pos[points['Thorax']]), (pos[points['AnotherShoulder']] - pos[points['Shoulder']]))
    orientation = QQuaternion.fromDirection(direction, up)
    rotation = upper_correctqq * orientation * shoulder_initial_orientation.inverted()
    # 肩ポーンの回転から親ボーンの回転を差し引いてbf.rotationに格納する。
    shoulder_rotation = upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation # 後で使うので保存しておく
    
    # 腕
    direction = pos[points['Elbow']] - pos[points['Shoulder']]
    up = QVector3D.crossProduct((pos[points['Elbow']] - pos[points['Shoulder']]), (pos[points['Wrist']] - pos[points['Elbow']]))
    orientation = QQuaternion.fromDirection(direction, up)
    rotation = upper_correctqq * orientation * arm_initial_orientation.inverted()
    # 腕ポーンの回転から親ボーンの回転を差し引いてbf.rotationに格納する。
    arm_rotation = shoulder_rotation.inverted() * upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation # 後で使うので保存しておく
    
    # ひじ
    direction = pos[points['Wrist']] - pos[points['Elbow']]
    up = QVector3D.crossProduct((pos[points['Elbow']] - pos[points['Shoulder']]), (pos[points['Wrist']] - pos[points['Elbow']]))
    orientation = QQuaternion.fromDirection(direction, up)
    rotation = upper_correctqq * orientation * arm_initial_orientation.inverted()
    # ひじポーンの回転から親ボーンの回転を差し引いてbf.rotationに格納する。
    # upper_body_rotation * left_shoulder_rotation * left_arm_rotation * bf.rotation = rotation なので、
    elbow_rotation = arm_rotation.inverted() * shoulder_rotation.inverted() * upper_body_rotation2.inverted() * upper_body_rotation1.inverted() * rotation
    # bf.rotation = (upper_body_rotation * left_arm_rotation).inverted() * rotation # 別の表現
    
    return shoulder_rotation, arm_rotation, elbow_rotation


# 片方の足のFK
def position_to_frame_leg_one_side(frame, pos, pos_gan, lower_correctqq, lower_body_rotation, points, bone_names, is_gan):

    if pos_gan is not None:
        # 足(3dpose-gan採用)
        leg_rotation, knee_rotation = \
            position_to_frame_leg_one_side_calc(frame, pos_gan, QQuaternion(), lower_body_rotation, points)

        # 体幹がgan採用もしくはオイラー角回転がどれか45度以上の場合、3dpose-gan採用
        if is_gan \
                or (abs(leg_rotation.toEulerAngles().x()) > 45 or abs(leg_rotation.toEulerAngles().y()) > 45 or abs(leg_rotation.toEulerAngles().z()) > 45 \
                or abs(knee_rotation.toEulerAngles().x()) > 45 or abs(knee_rotation.toEulerAngles().y()) > 45 or abs(knee_rotation.toEulerAngles().z()) > 45 ):
            return leg_rotation, knee_rotation
    
    # 3d-pose-baseline のFK
    leg_rotation, knee_rotation = \
        position_to_frame_leg_one_side_calc(frame, pos, lower_correctqq, lower_body_rotation, points)

    # 足の角度が大人しい場合、3d-pose-baseline を採用
    return leg_rotation, knee_rotation

# 片方の足の実体
def position_to_frame_leg_one_side_calc(frame, pos, lower_correctqq, lower_body_rotation, points):
    # 足
    direction = pos[points['Knee']] - pos[points['Hip']]
    up = QVector3D.crossProduct((pos[points['Knee']] - pos[points['Hip']]), (pos[points['Foot']] - pos[points['Knee']]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    leg_rotation = lower_body_rotation.inverted() * rotation
    
    # ひざ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x82\xd0\x82\xb4' # 'ひざ'
    direction = pos[points['Foot']] - pos[points['Knee']]
    up = QVector3D.crossProduct((pos[points['Knee']] - pos[points['Hip']]), (pos[points['Foot']] - pos[points['Knee']]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    knee_rotation = leg_rotation.inverted() * lower_body_rotation.inverted() * rotation

    return leg_rotation, knee_rotation
