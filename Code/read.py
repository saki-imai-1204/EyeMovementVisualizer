import pandas as pd
import numpy as np
import os

def read_EyeLink1000(filename, filepath):
    """Read asc file from Eye Link 1000 eye tracker and write a result in a csv file.
    Parameters
    ----------
    filename : str
        name of the asc file
    filepath : str
        filepath to write the csv file
        
    Returns
    -------
    pandas.DataFrame
        DataFrame with the data from the asc file
    """

    asc_file = open(filename)
    print("parsing file:", filename)

    text = asc_file.read()
    text_lines = text.split('\n')

    trial_id = -1
    participant_id = filename.split('.')[0]

    count = 0

    header = ["time_stamp", "eye_event", "x_cord", "y_cord", "duration", "pupil", "x1_cord", "y1_cord", "amplitude", "peak_velocity"]
    result = pd.DataFrame(columns=header)

    for line in text_lines:

        token = line.split()

        if not token:
            continue

        if "TRIALID" in token:
            # List of eye events
            if trial_id == -1:
                trial_id = int(token[-1])
                continue

            # Read image location
            index = str(int(trial_id) + 1)
            experiment = participant_id.split('/')[-1]
            location = 'datasets/AlMadi2018/AlMadi2018/runtime/dataviewer/' + experiment + '/graphics/VC_' + index + '.vcl'
            with open(location, 'r') as file:
                image = file.readlines()[1].split()[-3].split('/')[-1]

            count = 0
            trial_id = int(token[-1])

        if token[0] == "EFIX":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5])
            y_cord = float(token[6])
            pupil = int(token[7])

            df = pd.DataFrame([[timestamp,
                                    "fixation",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    pupil,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

        if token[0] == "ESACC":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5]) if token[5] != '.' else 0.0
            y_cord = float(token[6]) if token[6] != '.' else 0.0
            x1_cord = float(token[7]) if token[7] != '.' else 0.0
            y1_cord = float(token[8]) if token[8] != '.' else 0.0
            amplitude = float(token[9])
            peak_velocity = int(token[10])

            df = pd.DataFrame([[timestamp,
                                    "saccade",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    np.nan,
                                    x1_cord,
                                    y1_cord,
                                    amplitude,
                                    peak_velocity]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

        if token[0] == "EBLINK":
            timestamp = int(token[2])
            duration = int(token[4])

            df = pd.DataFrame([[timestamp,
                                    "blink",
                                    np.nan,
                                    np.nan,
                                    duration,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

    asc_file.close()

    result.to_csv(filepath + "df.csv")
    print("Wrote a csv file to: " + filepath + "df.csv")

    return result

print(read_EyeLink1000("\\Users\\PC\\Desktop\\Copy of Saki's results\\Results\\024_2\\024_2.asc", \
    "\\Users\\PC\\Desktop\\Copy of Saki's results\\Results\\024_2\\"))