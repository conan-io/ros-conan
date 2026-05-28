#include <tensorflow/lite/model.h>
#include <tensorflow/lite/interpreter.h>
#include <tensorflow/lite/kernels/register.h>
#include <tensorflow/lite/optional_debug_tools.h>
#include <tensorflow/lite/string_util.h>

#include <opencv2/videoio.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#include <iostream>
#include <fstream>
#include <memory>
#include <unordered_map>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "visualization_msgs/msg/marker_array.hpp"
#include "geometry_msgs/msg/point.hpp"

using visualization_msgs::msg::Marker;
using visualization_msgs::msg::MarkerArray;
using geometry_msgs::msg::Point;

struct Joint {
    std::string name;
    Point position;
    float confidence;
};

struct Bone {
    std::string name;
    int joint_a;
    int joint_b;
};

struct Skeleton {
    int num_joints = 17;
    std::unordered_map<int, Joint> joints;
    std::vector<Bone> bones;
};


using visualization_msgs::msg::Marker;
using visualization_msgs::msg::MarkerArray;

class HumanSkeletonPublisher : public rclcpp::Node {
private:
    rclcpp::Publisher<MarkerArray>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    std::shared_ptr<Skeleton> skeleton_;

    void publish_skeleton() {
        if (!skeleton_) {
            return;
        }

        const float confidence_threshold = 0.2;
        MarkerArray marker_array;
        rclcpp::Time now = this->now();
        int id = 0;

        double scale = 2.0;

        // === 1. Draw joints ===
        for (const auto &[id, joint] : skeleton_->joints) {
            if (joint.confidence > confidence_threshold) {
                Marker m;
                m.header.frame_id = "map";
                m.header.stamp = now;
                m.ns = "joints";
                m.id = id;
                m.type = Marker::SPHERE;
                m.action = Marker::ADD;
                m.pose.position.x = joint.position.x * scale;
                m.pose.position.y = 0.0;
                m.pose.position.z = (1.0 - joint.position.y) * scale;
                m.scale.x = m.scale.y = m.scale.z = 0.05;
                m.color.r = 1.0; m.color.g = 0.8; m.color.b = 0.2; m.color.a = 1.0;
                m.lifetime = rclcpp::Duration::from_seconds(0.5);
                marker_array.markers.push_back(m);
            }
        }

        // === 2. Draw bones ===
        Marker bone_lines;
        bone_lines.header.frame_id = "map";
        bone_lines.header.stamp = now;
        bone_lines.ns = "bones";
        bone_lines.id = id++;
        bone_lines.type = Marker::LINE_LIST;
        bone_lines.action = Marker::ADD;
        bone_lines.scale.x = 0.02;
        bone_lines.color.r = 0.0; bone_lines.color.g = 0.6; bone_lines.color.b = 1.0; bone_lines.color.a = 1.0;

        for (const auto &b : skeleton_->bones) {
            if (skeleton_->joints.count(b.joint_a) && skeleton_->joints.count(b.joint_b)) {
                if (skeleton_->joints[b.joint_a].confidence > confidence_threshold &&
                    skeleton_->joints[b.joint_b].confidence > confidence_threshold) {
                    Point position_a = skeleton_->joints[b.joint_a].position;
                    position_a.x = position_a.x * scale;
                    position_a.z = (1.0 - position_a.y) * scale;
                    position_a.y = 0.0;
                    bone_lines.points.push_back(position_a);
                    Point position_b = skeleton_->joints[b.joint_b].position;
                    position_b.x = position_b.x * scale;
                    position_b.z = (1.0 - position_b.y) * scale;
                    position_b.y = 0.0;
                    bone_lines.points.push_back(position_b);
                }
            }
        }

        marker_array.markers.push_back(bone_lines);
        publisher_->publish(marker_array);
    }

public:
    explicit HumanSkeletonPublisher(std::shared_ptr<Skeleton> skeleton)
    : Node("human_skeleton_publisher"), skeleton_(std::move(skeleton)) {
        publisher_ = this->create_publisher<MarkerArray>("human_skeleton_markers", 10);
        timer_ = this->create_wall_timer(
        std::chrono::milliseconds(200),
        std::bind(&HumanSkeletonPublisher::publish_skeleton, this));
    }
};

// The Output is a float32 tensor of shape [1, 1, 17, 3].

// The first two channels of the last dimension represents the yx coordinates (normalized
// to image frame, i.e. range in [0.0, 1.0]) of the 17 keypoints (in the order of: [nose,
// left eye, right eye, left ear, right ear, left shoulder, right shoulder, left elbow,
// right elbow, left wrist, right wrist, left hip, right hip, left knee, right knee, left
// ankle, right ankle]).

// The third channel of the last dimension represents the prediction confidence scores of
// each keypoint, also in the range [0.0, 1.0].

static Point make_point(double x, double y, double z) {
    Point p; p.x = x; p.y = y; p.z = z; return p;
}

std::shared_ptr<Skeleton> define_skeleton() {
    auto skeleton = std::make_shared<Skeleton>();

    // The Output of the tensorflow library is a float32 tensor of shape [1, 1, 17, 3].

    // The first two channels of the last dimension represents the yx coordinates (normalized
    // to image frame, i.e. range in [0.0, 1.0]) of the 17 keypoints (in the order of: [nose,
    // left eye, right eye, left ear, right ear, left shoulder, right shoulder, left elbow,
    // right elbow, left wrist, right wrist, left hip, right hip, left knee, right knee, left
    // ankle, right ankle]).

    // The third channel of the last dimension represents the prediction confidence scores of
    // each keypoint, also in the range [0.0, 1.0].

    skeleton->joints = {
        // FIXME: This initial coordinates are random
        {0, {"head", make_point(0.0, 0.0, 1.7), 0.0}},  // nose
        {5, {"left_shoulder", make_point(0.2, 0.0, 1.5), 0.0}},
        {6, {"right_shoulder", make_point(-0.2, 0.0, 1.5), 0.0}},
        {7, {"left_elbow", make_point(0.4, 0.0, 1.3), 0.0}},
        {8, {"right_elbow", make_point(-0.4, 0.0, 1.3), 0.0}},
        {9, {"left_wrist", make_point(0.6, 0.0, 1.1), 0.0}},
        {10, {"right_wrist", make_point(-0.6, 0.0, 1.1), 0.0}},
        {11, {"left_waist", make_point(0.15, 0.0, 1.0), 0.0}},
        {12, {"right_waist", make_point(-0.15, 0.0, 1.0), 0.0}},
        {13, {"left_knee", make_point(0.15, 0.0, 0.6), 0.0}},
        {14, {"right_knee", make_point(-0.15, 0.0, 0.6), 0.0}},
        {15, {"left_foot", make_point(0.15, 0.1, 0.0), 0.0}},
        {16, {"right_foot", make_point(-0.15, 0.1, 0.0), 0.0}}
    };

    skeleton->bones = {
        {"neck_left", 0, 5},
        {"neck_right", 0, 6},
        {"shoulders", 5, 6},
        {"left_upper_arm", 5, 7},
        {"left_forearm", 7, 9},
        {"right_upper_arm", 6, 8},
        {"right_forearm", 8, 10},
        {"left_torso", 5, 11},
        {"right_torso", 6, 12},
        {"waist", 11, 12},
        {"left_thigh", 11, 13},
        {"right_thigh", 12, 14},
        {"left_leg", 13, 15},
        {"right_leg", 14, 16}
    };

    return skeleton;
}

void update_skeleton(float *results, std::shared_ptr<Skeleton> sk) {
    for (int i = 0; i < sk->num_joints; ++i) {
        float y = results[i * 3];
        float x = results[i * 3 + 1];
        float confidence = results[i * 3 + 2];

        sk->joints[i].position = make_point(x, y, 0.0);
        sk->joints[i].confidence = confidence;
    }
}

void cv_draw_skeleton(cv::Mat &resized_image, std::shared_ptr<Skeleton> sk) {
    const float confidence_threshold = 0.2;
    int square_dim = resized_image.rows;

    for (int i = 0; i < sk->num_joints; ++i) {
        if (sk->joints[i].confidence > confidence_threshold) {
            int img_x = static_cast<int>(sk->joints[i].position.x * square_dim);
            int img_y = static_cast<int>(sk->joints[i].position.y * square_dim);
            cv::circle(resized_image, cv::Point(img_x, img_y), 2, cv::Scalar(255, 200, 200), 1);
        }
    }

    // draw skeleton
    for (const auto &bone : sk->bones) {
        int joint_a_id = bone.joint_a;
        float joint_a_x = sk->joints[joint_a_id].position.x;
        float joint_a_y = sk->joints[joint_a_id].position.y;
        float joint_a_confidence = sk->joints[joint_a_id].confidence;

        int joint_b_id = bone.joint_b;
        float joint_b_x = sk->joints[joint_b_id].position.x;
        float joint_b_y = sk->joints[joint_b_id].position.y;
        float joint_b_confidence = sk->joints[joint_b_id].confidence;

        if (joint_a_confidence > confidence_threshold && joint_b_confidence > confidence_threshold) {
            int img_x1 = static_cast<int>(joint_a_x * square_dim);
            int img_y1 = static_cast<int>(joint_a_y * square_dim);
            int img_x2 = static_cast<int>(joint_b_x * square_dim);
            int img_y2 = static_cast<int>(joint_b_y * square_dim);
            cv::line(resized_image, cv::Point(img_x1, img_y1), cv::Point(img_x2, img_y2), cv::Scalar(200, 200, 200), 1);
        }
    }
}


int main(int argc, char *argv[]) {

    rclcpp::init(argc, argv);

    // model from https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4
    // A convolutional neural network model that runs on RGB images and predicts human
    // joint locations of a single person. The model is designed to be run in the browser
    // using Tensorflow.js or on devices using TF Lite in real-time, targeting
    // movement/fitness activities. This variant: MoveNet.SinglePose.Lightning is a lower
    // capacity model (compared to MoveNet.SinglePose.Thunder) that can run >50FPS on most
    // modern laptops while achieving good performance.
    std::string model_file = "assets/lite-model_movenet_singlepose_lightning_tflite_float16_4.tflite";
    // Video by Olia Danilevich from https://www.pexels.com/
    std::string video_file = "assets/dancing.mp4";
    std::string image_file = "";
    bool show_windows = true;
    bool use_camera = false;

    std::map<std::string, std::string> arguments;

    for (int i = 1; i < argc; ++i) {
        std::string arg(argv[i]);

        if (arg.find("--") == 0) {
            size_t equal_sign_pos = arg.find("=");
            std::string key = arg.substr(0, equal_sign_pos);
            std::string value = equal_sign_pos != std::string::npos ? arg.substr(equal_sign_pos + 1) : "";

            arguments[key] = value;
        }
    }

    if (arguments.count("--model")) {
        model_file = arguments["--model"];
    }

    if (arguments.count("--video")) {
        video_file = arguments["--video"];
    }

    if (arguments.count("--image")) {
        image_file = arguments["--image"];
    }

    if (arguments.count("--camera")) {
        use_camera = true;
    }

    if (arguments.count("--no-windows")) {
        show_windows = false;
    }

    std::cout << "OpenCV version: " << CV_VERSION << std::endl;

    auto model = tflite::FlatBufferModel::BuildFromFile(model_file.c_str());

    if (!model) {
        throw std::runtime_error("Failed to load TFLite model");
    }

    tflite::ops::builtin::BuiltinOpResolver op_resolver;
    std::unique_ptr<tflite::Interpreter> interpreter;
    tflite::InterpreterBuilder(*model, op_resolver)(&interpreter);

    if (interpreter->AllocateTensors() != kTfLiteOk) {
        throw std::runtime_error("Failed to allocate tensors");
    }

    tflite::PrintInterpreterState(interpreter.get());

    auto input = interpreter->inputs()[0];
    auto input_batch_size = interpreter->tensor(input)->dims->data[0];
    auto input_height = interpreter->tensor(input)->dims->data[1];
    auto input_width = interpreter->tensor(input)->dims->data[2];
    auto input_channels = interpreter->tensor(input)->dims->data[3];

    std::cout << "The input tensor has the following dimensions: ["<< input_batch_size << "," 
                                                                   << input_height << "," 
                                                                   << input_width << ","
                                                                   << input_channels << "]" << std::endl;

    auto output = interpreter->outputs()[0];

    auto dim0 = interpreter->tensor(output)->dims->data[0];
    auto dim1 = interpreter->tensor(output)->dims->data[1];
    auto dim2 = interpreter->tensor(output)->dims->data[2];
    auto dim3 = interpreter->tensor(output)->dims->data[3];
    std::cout << "The output tensor has the following dimensions: ["<< dim0 << "," 
                                                                    << dim1 << "," 
                                                                    << dim2 << ","
                                                                    << dim3 << "]" << std::endl;


    cv::VideoCapture video;

    if (use_camera) {
        video.open(0);  // open default camera
    } else {
        video.open(video_file);
    }

    cv::Mat frame;

    if (image_file.empty()) {
        if (!video.isOpened()) {
            std::cout << "Can't open the video: " << video_file << std::endl;
            return -1;
        }
    }
    else {
        frame = cv::imread(image_file);


    }

    auto skeleton = define_skeleton();

    auto node = std::make_shared<HumanSkeletonPublisher>(skeleton);

    std::thread ros_thread([&]() {
        rclcpp::spin(node);
    });

    while (rclcpp::ok()) {

        if (image_file.empty()) {
            video >> frame;

            if (frame.empty()) {
                video.set(cv::CAP_PROP_POS_FRAMES, 0);
                continue;
            }
        }
        
        int image_width = frame.size().width;
        int image_height = frame.size().height;

        int square_dim = std::min(image_width, image_height);
        int delta_height = (image_height - square_dim) / 2;
        int delta_width = (image_width - square_dim) / 2;

        cv::Mat resized_image;

        // crop + resize the input image
        cv::resize(frame(cv::Rect(delta_width, delta_height, square_dim, square_dim)), resized_image, cv::Size(input_width, input_height));

        memcpy(interpreter->typed_input_tensor<unsigned char>(0), resized_image.data, resized_image.total() * resized_image.elemSize());

        // inference
        std::chrono::steady_clock::time_point start, end;
        start = std::chrono::steady_clock::now();
        if (interpreter->Invoke() != kTfLiteOk) {
            std::cerr << "Inference failed" << std::endl;
            return -1;
        }
        end = std::chrono::steady_clock::now();
        auto processing_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

        std::cout << "processing time: " << processing_time << " ms" << std::endl;

        float *results = interpreter->typed_output_tensor<float>(0);

        update_skeleton(results, skeleton);

        // Resize for better visualization
        cv::Mat upscaled_image;
        cv::resize(resized_image, upscaled_image, cv::Size(square_dim*1.6, square_dim*1.6));

        cv_draw_skeleton(upscaled_image, skeleton);

        if (show_windows) {
            imshow("Output", upscaled_image);
        }
        else {
            // just run one frame when not showing output
            break;
        }

        int waitTime;
        // render at 30 fps
        if (use_camera) {
            waitTime = 1;
        }
        else {
            waitTime = processing_time<33 ? 33-processing_time : 1;
        }

        if (cv::waitKey(waitTime) >= 0) {
            break;
        }
    }

    if (image_file.empty()) {
        video.release();
    }

    rclcpp::shutdown();
    ros_thread.join();

    if (show_windows) {
        cv::destroyAllWindows();
    }

    return 0;
}
