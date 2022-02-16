from __future__ import annotations

import typing
from typing import Optional

import numpy as np
import pandas as pd
import scipy.fft

from endaq.calc import psd, utils


__all__ = ["aggregate_fft", "fft", "rfft", "dct", "dst"]


def aggregate_fft(df, **kwargs):
    """
    Calculate the FFT using :py:func:`scipy.signal.welch` with a specified frequency spacing.  The data returned is in the same
    units as the data input.

    :param df: The input data
    :param bin_width: The desired width of the resulting frequency bins, in Hz;
        defaults to 1 Hz
    :param kwargs: Other parameters to pass directly to :py:func:`scipy.signal.welch`
    :return: A periodogram of the input data in the same units as the input.

    .. seealso::

        - `SciPy Welch's method <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_
          Documentation for the periodogram function wrapped internally.
    """
    kwargs['scaling'] = 'unit'
    kwargs['window'] = 'boxcar'
    kwargs['noverlap'] = 0
    return psd.welch(df, **kwargs)


def fft(
        df: pd.DataFrame,
        output: typing.Literal[None, "magnitude", "angle", "complex"] = None,
        nfft: Optional[int] = None,
        norm: typing.Literal[None, "unit", "forward", "ortho", "backward"] = None,
        optimize: bool = True,
    ) -> pd.DataFrame:
    """
    Perform the FFT of the data in ``df``, using SciPy's FFT method from :py:func:`scipy.fft.fft`.  If the in ``df`` is all real,
    then the output will be symmetrical between positive and negative frequencies, and it is instead recommended that
    you use the :py:func:`endaq.calc.fft.fft` method.

    :param df: The input data
    :param output: The type of the output of the FFT. Default is "magnitude".  "magnitude" will return the
                   absolute value of the FFT, "angle" will return the phase angle in radians, "complex" will return the
                   complex values of the FFT.
    :param nfft: Length of the transformed axis of the output. If nfft is smaller than the length of the
                 input, the input is cropped. If it is larger, the input is padded with zeros. If n is not given, the
                 length of the input along the axis specified by axis is used.
    :param norm: Normalization mode. Default is "unit", meaning a normalization of 2/n is applied on the
                 forward transform, and a normalization of 1/2 is applied on the ``ifft``. The "unit" normalization means
                 that the units of the FFT are the same as the units of the data put into it and that a sinusoid of
                 amplitude A will peak with amplitude A in the frequency domain.  “forward” instead applies a
                 normalization of 1/n on the forward transforms and no normalization is applied on the ``ifft``. “backward”
                 applies no normalization on the forward transform and 1/n on the backward. For ``norm="ortho"``, both
                 directions are scaled by `1/sqrt(n)`.
    :param optimize: If optimize is set to True, the length of the FFT will automatically be padded to a
                     length which can be calculated more quickly.  Default is True.
    :param kwargs: Further keywords passed to :py:func:`scipy.fft.fft`.  Note that the nfft parameter of this function is passed
                   to :py:func:`scipy.fft.fft` as ``n``.
    :return: The FFT of each channel in ``df``.

    .. seealso::

        - `SciPy FFT method <https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.fft.fft.html>`_
          Documentation for the FFT function wrapped internally.
    """
    if output is None:
        output_fun = np.abs
    elif output not in ["magnitude", "angle", "complex"]:
        raise ValueError(f'output must be one of None, "magnitude", "angle", or "complex".  Was {output}.')
    else:
        if output == "magnitude":
            output_fun = np.abs
        elif output == "angle":
            output_fun = np.angle
            norm = "forward"  # this prevents scaling when the angle is calculated
        elif output == "complex":
            output_fun = np.asarray
        else:
            raise Exception("impossible state reached in fft output type")

    if nfft is None:
        nfft = len(df)
    elif not isinstance(nfft, int):
        raise TypeError(f'nfft must be a positive integer, was of type {type(nfft)}')
    elif nfft <= 0:
        raise ValueError(f'nfft must be positive, was {nfft}')

    if optimize:
        nfft = scipy.fft.next_fast_len(nfft, False)

    scale = 1.
    if norm is None:
        norm = "forward"
        scale = 2.
    elif norm == "unit":
        norm = "forward"
        scale = 2.
    elif norm not in ["forward", "ortho", "backward"]:
        raise ValueError(f'norm must be one of None, "forward", "ortho", or "backward".  Was {norm}.')

    dt = utils.sample_spacing(df)

    data = {
            c: output_fun(scipy.fft.fftshift(scipy.fft.fft(
                df[c].to_numpy(),
                n=nfft,
                norm=norm,
            )))*scale
            for c in df.columns}
    index = pd.Index(scipy.fft.fftshift(scipy.fft.fftfreq(nfft, dt)), name='frequency (Hz)')

    return pd.DataFrame(
        data=data,
        columns=df.columns,
        index=index,
    )


def rfft(
        df: pd.DataFrame,
        output: typing.Literal[None, "magnitude", "angle", "complex"] = None,
        nfft: Optional[int] = None,
        norm: typing.Literal[None, "unit", "forward", "ortho", "backward"] = None,
        optimize: bool = True,
    ) -> pd.DataFrame:
    """
    Perform the real valued FFT of the data in ``df``, using SciPy's RFFT method from :py:func:`scipy.fft.rfft`.

    :param df: The input data
    :param output: The type of the output of the FFT. Default is "magnitude".  "magnitude" will return the
                   absolute value of the FFT, "angle" will return the phase angle in radians, "complex" will return the
                   complex values of the FFT.
    :param nfft: Length of the transformed axis of the output. If nfft is smaller than the length of the
                 input, the input is cropped. If it is larger, the input is padded with zeros. If n is not given, the
                 length of the input along the axis specified by axis is used.
    :param norm: Normalization mode. Default is "unit", meaning a normalization of 2/n is applied on the
                 forward transform, and a normalization of 1/2 is applied on the ``ifft``. The "unit" normalization means
                 that the units of the FFT are the same as the units of the data put into it and that a sinusoid of
                 amplitude A will peak with amplitude A in the frequency domain.  “forward” instead applies a
                 normalization of 1/n on the forward transforms and no normalization is applied on the ``ifft``. “backward”
                 applies no normalization on the forward transform and 1/n on the backward. For ``norm="ortho"``, both
                 directions are scaled by `1/sqrt(n)`.
    :param optimize: If optimize is set to True, the length of the FFT will automatically be padded to a
                     length which can be calculated more quickly.  Default is True.
    :param kwargs: Further keywords passed to :py:func:`scipy.fft.rfft`.  Note that the nfft parameter of this function is passed
                   to :py:func:`scipy.fft.rfft` as ``n``.
    :return: The RFFT of each channel in ``df``.

    .. seealso::

        - `SciPy RFFT method <https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.fft.rfft.html>`_
          Documentation for the RFFT function wrapped internally.
    """

    if output is None:
        output_fun = np.abs
    elif output not in ["magnitude", "angle", "complex"]:
        raise ValueError(f'output must be one of None, "magnitude", "angle", or "complex".  Was {output}.')
    else:
        if output == "magnitude":
            output_fun = np.abs
        elif output == "angle":
            output_fun = np.angle
            norm = "forward"  # this prevents scaling when the angle is calculated
        elif output == "complex":
            output_fun = np.asarray
        else:
            raise Exception("impossible state reached in fft output type")

    if nfft is None:
        nfft = len(df)
    elif not isinstance(nfft, int):
        raise TypeError(f'nfft must be a positive integer, was of type {type(nfft)}')
    elif nfft <= 0:
        raise ValueError(f'nfft must be positive, was {nfft}')

    if optimize:
        nfft = scipy.fft.next_fast_len(nfft, True)

    scale = 1.
    if norm is None:
        norm = "forward"
        scale = 2.
    elif norm == "unit":
        norm = "forward"
        scale = 2.
    elif norm not in ["forward", "ortho", "backward"]:
        raise ValueError(f'norm must be one of None, "forward", "ortho", or "backward".  Was {norm}.')

    dt = utils.sample_spacing(df)

    data = {
            c: output_fun(scipy.fft.rfft(
                df[c].to_numpy(),
                n=nfft,
                norm=norm,
            ))*scale
            for c in df.columns}
    index = pd.Index(scipy.fft.rfftfreq(nfft, dt), name='frequency (Hz)')

    return pd.DataFrame(
        data=data,
        columns=df.columns,
        index=index,
    )


def dct(
        df: pd.DataFrame,
        nfft: Optional[int] = None,
        norm: typing.Literal[None, "unit", "forward", "ortho", "backward"] = None,
        **kwargs,
    ) -> pd.DataFrame:
    """
    Calculate the DCT of the data in ``df``, using SciPy's DCT method from :py:func:`scipy.fft.dct`.

    :param df: the input data
    :param nfft: Length of the transformed axis of the output. If nfft is smaller than the length of the
                 input, the input is cropped. If it is larger, the input is padded with zeros. If n is not given, the
                 length of the input along the axis specified by axis is used.
    :param norm: Normalization mode. Default is "unit", meaning a normalization of 2/n is applied on the
                 forward transform, and a normalization of 1/2 is applied on the ``idct``. The "unit" normalization means
                 that the units of the FFT are the same as the units of the data put into it and that a sinusoid of
                 amplitude A will peak with amplitude A in the frequency domain.  “forward” instead applies a
                 normalization of 1/n on the forward transforms and no normalization is applied on the ``idct``. “backward”
                 applies no normalization on the forward transform and 1/n on the backward. For ``norm="ortho"``, both
                 directions are scaled by `1/sqrt(n)`.
    :param kwargs: Further keywords passed to :py:func:`scipy.fft.dct`.  Note that the nfft parameter of this function
                   is passed to :py:func:`scipy.fft.dct` as ``n``.
    :return: The DCT of each channel in ``df``.

    .. seealso::

        - `SciPy DCT method <https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.fft.dct.html>`_
          Documentation for the DCT function wrapped internally.
    """

    if nfft is None:
        nfft = len(df)
    elif not isinstance(nfft, int):
        raise TypeError(f'nfft must be a positive integer, was of type {type(nfft)}')
    elif nfft <= 0:
        raise ValueError(f'nfft must be positive, was {nfft}')

    scale = 1.

    if norm is None:
        norm = "forward"
        scale = 2.
    elif norm == "unit":
        norm = "forward"
        scale = 2.
    elif norm not in ["forward", "ortho", "backward"]:
        raise ValueError(f'norm must be one of None, "forward", "ortho", or "backward".  Was {norm}.')

    dt = utils.sample_spacing(df)
    fs = 1./dt

    return pd.DataFrame(
        data={
            c: scipy.fft.dst(
                df[c].to_numpy(),
                n=nfft,
                norm=norm,
                **kwargs,
            )*scale
            for c in df.columns},
        columns=df.columns,
        index=np.linspace(0, fs/2, nfft),
    )


def dst(
        df: pd.DataFrame,
        nfft: Optional[int] = None,
        norm: typing.Literal[None, "unit", "forward", "ortho", "backward"] = None,
        **kwargs,
    ) -> pd.DataFrame:
    """
    Calculate the DST of the data in ``df``, using SciPy's DST method from :py:func:`scipy.fft.dst`.

    :param df: the input data
    :param nfft: Length of the transformed axis of the output. If nfft is smaller than the length of the
                 input, the input is cropped. If it is larger, the input is padded with zeros. If n is not given, the
                 length of the input along the axis specified by axis is used.
    :param norm: Normalization mode. Default is "unit", meaning a normalization of 2/n is applied on the
                 forward transform, and a normalization of 1/2 is applied on the ``idst``. The "unit" normalization means
                 that the units of the FFT are the same as the units of the data put into it and that a sinusoid of
                 amplitude A will peak with amplitude A in the frequency domain.  “forward” instead applies a
                 normalization of 1/n on the forward transforms and no normalization is applied on the ``idst``. “backward”
                 applies no normalization on the forward transform and 1/n on the backward. For ``norm="ortho"``, both
                 directions are scaled by `1/sqrt(n)`.
    :param kwargs: Further keywords passed to :py:func:`scipy.fft.dst`.  Note that the nfft parameter of this function is passed
                   to :py:func:`scipy.fft.dst` as ``n``.
    :return: The DST of each channel in ``df``.

    .. seealso::

        - `SciPy DST method <https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.fft.dst.html>`_
          Documentation for the DST function wrapped internally.
    """

    if nfft is None:
        nfft = len(df)
    elif not isinstance(nfft, int):
        raise TypeError(f'nfft must be a positive integer, was of type {type(nfft)}')
    elif nfft <= 0:
        raise ValueError(f'nfft must be positive, was {nfft}')

    scale = 1.

    if norm is None:
        norm = "forward"
        scale = 2.
    elif norm == "unit":
        norm = "forward"
        scale = 2.
    elif norm not in ["forward", "ortho", "backward"]:
        raise ValueError(f'norm must be one of None, "forward", "ortho", or "backward".  Was {norm}.')

    dt = utils.sample_spacing(df)
    fs = 1./dt

    return pd.DataFrame(
        data={
            c: scipy.fft.dct(
                df[c].to_numpy(),
                n=nfft,
                norm=norm,
                **kwargs,
            )*scale
            for c in df.columns},
        columns=df.columns,
        index=np.linspace(0, fs/2, nfft),
    )
