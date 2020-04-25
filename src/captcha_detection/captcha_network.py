import os

import numpy as np
import tensorflow as tf
from tensorflow_core.python.keras.utils.vis_utils import plot_model

from accuracy.correctly_classified_captcha_accuracy import CorrectlyClassifiedCaptchaAccuracy
from dataset.data_batcher import DataBatcher


class CaptchaNetwork:
    def __init__(self, image_shape, classes: int, image_preprocess_pipeline, label_preprocess_pipeline, args):
        self._image_preprocess_pipeline = image_preprocess_pipeline
        self._label_preprocess_pipeline = label_preprocess_pipeline

        self._classes = classes
        input_shape = (image_shape[0], image_shape[1], 1)

        input = tf.keras.layers.Input(shape=input_shape)

        layer = input
        layer = tf.keras.layers.Convolution2D(
            filters=32, kernel_size=7, strides=2, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)
        layer = tf.keras.layers.MaxPooling2D(strides=2)(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=32, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=32, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=32, kernel_size=3, strides=2, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=64, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=64, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=64, kernel_size=3, strides=2, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=128, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=128, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=128, kernel_size=3, strides=2, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.Convolution2D(
            filters=256, kernel_size=3, strides=1, padding="same", use_bias=False,
            kernel_regularizer=tf.keras.regularizers.l2(args.l2))(layer)
        layer = tf.keras.layers.BatchNormalization()(layer)
        layer = tf.keras.layers.ReLU()(layer)

        layer = tf.keras.layers.GlobalAveragePooling2D()(layer)

        # # reshape into (batch, letters_count, rest)
        target_shape = (args.captcha_length, layer.shape[1] // args.captcha_length)
        layer = tf.keras.layers.Reshape(target_shape=target_shape)(layer)

        # layer = tf.keras.layers.Dense(units=100, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.01))(layer)
        # layer = tf.keras.layers.Dropout(0.5)(layer)
        output = tf.keras.layers.Dense(units=classes, activation="softmax")(layer)

        self._model = tf.keras.Model(inputs=input, outputs=output)
        self._loss = tf.keras.losses.SparseCategoricalCrossentropy()
        self._optimizer = tf.keras.optimizers.Adam()

        self._model.summary()
        plot_model(self._model, to_file=os.path.join(args.out_dir, "model.png"), show_shapes=True)

        self._metrics = {
            "loss": tf.metrics.Mean(),
            "accuracy": tf.keras.metrics.SparseCategoricalAccuracy(),
            "correct_accuracy": CorrectlyClassifiedCaptchaAccuracy()
        }
        self._validation_metrics = {
            "loss": tf.metrics.Mean(),
            "accuracy": tf.keras.metrics.SparseCategoricalAccuracy(),
            "correct_accuracy": CorrectlyClassifiedCaptchaAccuracy()
        }
        self._writer = tf.summary.create_file_writer(args.logdir, flush_millis=10 * 1000)

        if args.weights_file is not None:
            self._model.load_weights(args.weights_file)

    def train(self, train_x, train_y, val_x, val_y, args):
        train_inputs, train_labels = self._image_preprocess_pipeline(train_x), self._label_preprocess_pipeline(train_y)
        dev_inputs, dev_labels = self._image_preprocess_pipeline(val_x), self._label_preprocess_pipeline(
            val_y)

        for epoch in range(args.epochs):
            self._train_epoch(train_inputs, train_labels, args.batch_size)
            self._evaluate_epoch(dev_inputs, dev_labels, args.batch_size)

            train_loss = self._metrics["loss"].result()
            train_acc = self._metrics["accuracy"].result()
            train_correct_acc = self._metrics["correct_accuracy"].result()

            dev_loss = self._validation_metrics["loss"].result()
            dev_acc = self._validation_metrics["accuracy"].result()
            dev_correct_acc = self._validation_metrics["correct_accuracy"].result()

            print(
                f"\rEpoch: {epoch + 1}, train-loss: {train_loss:.4f}, train-acc: {train_acc:.4f}, train-correct-acc: {train_correct_acc:.4f}, "
                f"dev-loss: {dev_loss:.4f}, dev-acc: {dev_acc:.4f}, dev-correct-acc: {dev_correct_acc:.4f}", flush=True)

            if (epoch + 1) % args.checkpoint_freq == 0:
                self._model.save_weights(f"{args.logdir}/{epoch + 1}.h5")

    def save_model(self, out_path):
        tf.saved_model.save(self._model, out_path)

    def _train_epoch(self, inputs, labels, batch_size):
        for i, (batch_inputs, batch_labels) in enumerate(DataBatcher(batch_size, inputs, labels).batches()):
            self._train_batch(batch_inputs, batch_labels)

            current_loss = self._metrics["loss"].result()
            current_acc = self._metrics["accuracy"].result()
            print(
                '\rBatch: {0}/{1}, loss: {2:.4f}, acc: {3:.4f}'.format(i * batch_size, len(inputs), current_loss,
                                                                       current_acc), flush=True, end="")

    def _evaluate_epoch(self, inputs, labels, batch_size):
        for i, (batch_inputs, batch_labels) in enumerate(DataBatcher(batch_size, inputs, labels).batches()):
            self._evaluate_batch(batch_inputs, batch_labels)

    @tf.function
    def _evaluate_batch(self, batch_inputs, batch_labels):
        logits = self._model(batch_inputs, training=False)
        batch_labels = tf.squeeze(batch_labels)
        loss = self._loss(batch_labels, logits)

        tf.summary.experimental.set_step(self._optimizer.iterations)
        with self._writer.as_default():
            for name, metric in self._validation_metrics.items():
                metric.reset_states()
                if name == "loss":
                    metric(loss)
                else:
                    metric.update_state(y_true=batch_labels, y_pred=logits)
                tf.summary.scalar("dev/{}".format(name), metric.result())

    @tf.function
    def _train_batch(self, inputs, labels):
        with tf.GradientTape() as tape:
            logits = self._model(inputs, training=True)
            labels = tf.squeeze(labels)

            loss = self._loss(labels, logits)
            loss = tf.reduce_mean(loss)

        gradients = tape.gradient(target=loss, sources=self._model.trainable_variables)
        self._optimizer.apply_gradients(zip(gradients, self._model.trainable_variables))

        tf.summary.experimental.set_step(self._optimizer.iterations)
        with self._writer.as_default():
            for name, metric in self._metrics.items():
                metric.reset_states()
                if name == "loss":
                    metric(loss)
                else:
                    metric.update_state(y_true=labels, y_pred=logits)
                tf.summary.scalar("train/{}".format(name), metric.result())

    def predict(self, inputs):
        inputs = self._image_preprocess_pipeline(inputs)

        return self._predict(inputs).numpy()

    @tf.function
    def _predict(self, inputs):
        y_pred = self._predict_proba(inputs)

        if len(y_pred.shape) <= 2:
            y_pred = tf.expand_dims(y_pred, axis=1)
        y_pred = tf.argmax(y_pred, axis=2)

        return y_pred

    def predict_proba(self, inputs):
        inputs = self._image_preprocess_pipeline(inputs)

        return self._predict_proba(inputs).numpy()

    @tf.function
    def _predict_proba(self, inputs):
        return self._model(inputs)